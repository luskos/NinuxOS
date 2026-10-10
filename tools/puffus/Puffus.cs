// Puffus.cs - Puffus for Windows (NinuxOS v2.9.60): build disk.img and write it onto a USB stick,
// sector for sector from the first one - the stick then starts NinuxOS on a PC.
//
//   tools\puffus\make_puffus.cmd      compiles it into Puffus.exe in the project folder
//
// It runs as Administrator (raw disk access). Only USB disks are offered. Before writing it locks
// and dismounts every drive letter of the stick; after writing it reads the stick back, compares,
// and ejects it - Windows must not mount a NinuxOS stick: the boot sector looks like a FAT12
// diskette and Windows writes "System Volume Information" over the kernel.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Management;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;
using Microsoft.Win32.SafeHandles;

static class Native
{
    public const uint GENERIC_READ = 0x80000000, GENERIC_WRITE = 0x40000000;
    public const uint SHARE_READ_WRITE = 3, OPEN_EXISTING = 3;
    public const uint FSCTL_LOCK_VOLUME = 0x00090018;
    public const uint FSCTL_DISMOUNT_VOLUME = 0x00090020;
    public const uint IOCTL_STORAGE_GET_DEVICE_NUMBER = 0x002D1080;
    public const uint IOCTL_STORAGE_EJECT_MEDIA = 0x002D4808;
    public const uint FILE_DEVICE_DISK = 7;

    [StructLayout(LayoutKind.Sequential)]
    public struct STORAGE_DEVICE_NUMBER
    {
        public uint DeviceType;
        public uint DeviceNumber;
        public uint PartitionNumber;
    }

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern SafeFileHandle CreateFile(string name, uint access, uint share, IntPtr security,
                                                   uint disposition, uint flags, IntPtr template);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool DeviceIoControl(SafeFileHandle h, uint code, IntPtr inBuf, uint inLen,
                                              IntPtr outBuf, uint outLen, out uint returned, IntPtr overlapped);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool DeviceIoControl(SafeFileHandle h, uint code, IntPtr inBuf, uint inLen,
                                              out STORAGE_DEVICE_NUMBER outBuf, uint outLen, out uint returned, IntPtr overlapped);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool FlushFileBuffers(SafeFileHandle h);

    public static bool Control(SafeFileHandle h, uint code)
    {
        uint returned;
        return DeviceIoControl(h, code, IntPtr.Zero, 0, IntPtr.Zero, 0, out returned, IntPtr.Zero);
    }
}

class UsbDisk
{
    public int Index;
    public string Model;
    public long Size;

    public override string ToString()
    {
        return string.Format("Disk {0}:  {1}  ({2:0.0} GB)", Index, Model, Size / 1073741824.0);
    }
}

class PuffusForm : Form
{
    const int SECTOR = 512;
    const int CHUNK = 1 << 20;

    readonly string root = Application.StartupPath;
    readonly ComboBox disks = new ComboBox();
    readonly Button refresh = new Button();
    readonly CheckBox build = new CheckBox();
    readonly Button write = new Button();
    readonly ProgressBar bar = new ProgressBar();
    readonly TextBox log = new TextBox();
    readonly BackgroundWorker worker = new BackgroundWorker();

    public PuffusForm()
    {
        Text = "Puffus - NinuxOS on a USB stick";
        ClientSize = new Size(620, 420);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 9f);

        Label l = new Label();
        l.Text = "USB stick (everything on it is erased):";
        l.SetBounds(12, 12, 400, 18);
        disks.DropDownStyle = ComboBoxStyle.DropDownList;
        disks.SetBounds(12, 34, 500, 24);
        refresh.Text = "Look again";
        refresh.SetBounds(520, 33, 88, 26);
        refresh.Click += delegate { FindDisks(); };

        build.Text = "Build disk.img first  (python tools\\build_disk.py)";
        build.Checked = true;
        build.SetBounds(12, 68, 400, 22);
        write.Text = "Write NinuxOS to the stick";
        write.SetBounds(12, 98, 220, 32);
        write.Click += delegate { Start(); };
        bar.SetBounds(244, 102, 364, 24);

        log.Multiline = true;
        log.ReadOnly = true;
        log.ScrollBars = ScrollBars.Vertical;
        log.Font = new Font("Consolas", 9f);
        log.SetBounds(12, 142, 596, 266);

        Controls.AddRange(new Control[] { l, disks, refresh, build, write, bar, log });

        worker.WorkerReportsProgress = true;
        worker.DoWork += Work;
        worker.ProgressChanged += delegate(object s, ProgressChangedEventArgs e)
        {
            bar.Value = Math.Max(0, Math.Min(100, e.ProgressPercentage));
            if (e.UserState != null) Say((string)e.UserState);
        };
        worker.RunWorkerCompleted += delegate(object s, RunWorkerCompletedEventArgs e)
        {
            if (e.Error != null) Say("STOPPED: " + e.Error.Message);
            write.Enabled = refresh.Enabled = disks.Enabled = build.Enabled = true;
            FindDisks();
        };

        Say("The project: " + root);
        Say("A NinuxOS stick must not be put back into Windows: Windows takes it for a FAT12");
        Say("diskette and writes its own folder over the kernel. Puffus ejects it when done.");
        FindDisks();
    }

    void Say(string line)
    {
        log.AppendText(line + "\r\n");
    }

    void FindDisks()
    {
        disks.Items.Clear();
        try
        {
            ManagementObjectSearcher q = new ManagementObjectSearcher(
                "SELECT Index, Model, Size FROM Win32_DiskDrive WHERE InterfaceType = 'USB'");
            foreach (ManagementObject d in q.Get())
            {
                if (d["Size"] == null) continue;            // a card reader with nothing in it
                UsbDisk u = new UsbDisk();
                u.Index = Convert.ToInt32(d["Index"]);
                u.Model = Convert.ToString(d["Model"]);
                u.Size = Convert.ToInt64(d["Size"]);
                disks.Items.Add(u);
            }
        }
        catch (Exception e)
        {
            Say("Cannot list the disks: " + e.Message);
        }
        if (disks.Items.Count > 0) disks.SelectedIndex = 0;
        else Say("No USB disk is plugged in.");
        write.Enabled = disks.Items.Count > 0;
    }

    void Start()
    {
        UsbDisk u = disks.SelectedItem as UsbDisk;
        if (u == null) return;
        if (!build.Checked && !File.Exists(Path.Combine(root, "disk.img")))
        {
            Say("There is no disk.img in the project - tick 'Build disk.img first'.");
            return;
        }
        string ask = "Everything on this disk will be erased:\r\n\r\n    " + u + "\r\n\r\nWrite NinuxOS onto it?";
        if (MessageBox.Show(this, ask, "Puffus", MessageBoxButtons.YesNo, MessageBoxIcon.Warning,
                            MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
        write.Enabled = refresh.Enabled = disks.Enabled = build.Enabled = false;
        bar.Value = 0;
        worker.RunWorkerAsync(new object[] { u, build.Checked });
    }

    void Work(object sender, DoWorkEventArgs e)
    {
        object[] args = (object[])e.Argument;
        UsbDisk u = (UsbDisk)args[0];
        if ((bool)args[1]) Build();
        WriteImage(u, Path.Combine(root, "disk.img"));
    }

    void Build()
    {
        worker.ReportProgress(0, "Building disk.img ...");
        ProcessStartInfo si = new ProcessStartInfo("python", "\"" + Path.Combine("tools", "build_disk.py") + "\"");
        si.WorkingDirectory = root;
        si.UseShellExecute = false;
        si.CreateNoWindow = true;
        si.RedirectStandardOutput = true;
        si.RedirectStandardError = true;
        StringBuilder errors = new StringBuilder();
        Process p;
        try
        {
            p = new Process();
            p.StartInfo = si;
            p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs d) { if (d.Data != null) errors.AppendLine(d.Data); };
            p.Start();
        }
        catch (Win32Exception)
        {
            throw new Exception("python was not found (it runs tools\\build_disk.py). Install Python or untick the build.");
        }
        p.BeginErrorReadLine();
        string output = p.StandardOutput.ReadToEnd();
        p.WaitForExit();
        foreach (string line in (output + errors).Replace("\r", "").Split('\n'))
            if (line.Length > 0) worker.ReportProgress(0, "  " + line);
        if (p.ExitCode != 0) throw new Exception("the build failed - nothing was written to the stick.");
    }

    void WriteImage(UsbDisk u, string image)
    {
        byte[] data = File.ReadAllBytes(image);
        if (data.Length % SECTOR != 0) Array.Resize(ref data, (data.Length / SECTOR + 1) * SECTOR);
        if (data.Length < SECTOR || data[510] != 0x55 || data[511] != 0xAA)
            throw new Exception("disk.img has no boot sector (55 AA) - not written.");
        if (data.Length > u.Size)
            throw new Exception("disk.img is bigger than the stick.");

        List<SafeFileHandle> volumes = new List<SafeFileHandle>();
        try
        {
            // every drive letter that lies on this disk: lock it and take it away from Windows
            foreach (DriveInfo d in DriveInfo.GetDrives())
            {
                string letter = d.Name.Substring(0, 2);
                SafeFileHandle v = Native.CreateFile("\\\\.\\" + letter, Native.GENERIC_READ | Native.GENERIC_WRITE,
                                                     Native.SHARE_READ_WRITE, IntPtr.Zero, Native.OPEN_EXISTING, 0, IntPtr.Zero);
                if (v.IsInvalid) continue;
                Native.STORAGE_DEVICE_NUMBER n;
                uint returned;
                bool ours = Native.DeviceIoControl(v, Native.IOCTL_STORAGE_GET_DEVICE_NUMBER, IntPtr.Zero, 0, out n,
                                                   (uint)Marshal.SizeOf(typeof(Native.STORAGE_DEVICE_NUMBER)), out returned, IntPtr.Zero)
                            && n.DeviceType == Native.FILE_DEVICE_DISK && n.DeviceNumber == (uint)u.Index;
                if (!ours)
                {
                    v.Close();
                    continue;
                }
                volumes.Add(v);
                if (!Native.Control(v, Native.FSCTL_LOCK_VOLUME))
                    throw new Exception("drive " + letter + " of the stick is in use - close what has it open and try again.");
                Native.Control(v, Native.FSCTL_DISMOUNT_VOLUME);
                worker.ReportProgress(0, "Drive " + letter + " locked and dismounted.");
            }

            SafeFileHandle h = Native.CreateFile("\\\\.\\PhysicalDrive" + u.Index, Native.GENERIC_READ | Native.GENERIC_WRITE,
                                                 Native.SHARE_READ_WRITE, IntPtr.Zero, Native.OPEN_EXISTING, 0, IntPtr.Zero);
            if (h.IsInvalid)
                throw new Exception("cannot open the stick: " + new Win32Exception(Marshal.GetLastWin32Error()).Message);
            using (FileStream f = new FileStream(h, FileAccess.ReadWrite, 4096, false))
            {
                worker.ReportProgress(0, string.Format("Writing {0} sectors ({1:0.0} MB) ...", data.Length / SECTOR, data.Length / 1048576.0));
                try
                {
                    for (int o = 0; o < data.Length; o += CHUNK)
                    {
                        f.Write(data, o, Math.Min(CHUNK, data.Length - o));
                        worker.ReportProgress((int)(o * 50L / data.Length));
                    }
                    f.Flush();
                    Native.FlushFileBuffers(h);
                }
                catch (IOException x)
                {
                    throw new Exception("writing failed: " + x.Message + "  (If USB sticks are write-protected on this PC: "
                        + "HKLM\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies, WriteProtect = 0, then plug the stick in again.)");
                }

                worker.ReportProgress(50, "Reading it back ...");
                f.Seek(0, SeekOrigin.Begin);
                byte[] back = new byte[CHUNK];
                for (int o = 0; o < data.Length; o += CHUNK)
                {
                    int want = Math.Min(CHUNK, data.Length - o);
                    int got = 0;
                    while (got < want)
                    {
                        int n = f.Read(back, got, want - got);
                        if (n <= 0) throw new Exception("the stick stopped answering while it was read back.");
                        got += n;
                    }
                    for (int i = 0; i < want; i++)
                        if (back[i] != data[o + i])
                            throw new Exception(string.Format("the stick does not hold what was written (sector {0}) - try another stick.", (o + i) / SECTOR));
                    worker.ReportProgress(50 + (int)(o * 50L / data.Length));
                }

                bool ejected = Native.Control(volumes.Count > 0 ? volumes[0] : h, Native.IOCTL_STORAGE_EJECT_MEDIA);
                worker.ReportProgress(100, "Done: the stick holds NinuxOS and was checked.");
                worker.ReportProgress(100, ejected ? "It is ejected - take it out."
                                                   : "Take it out now (it could not be ejected by itself).");
            }
        }
        finally
        {
            foreach (SafeFileHandle v in volumes) v.Close();
        }
    }

    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.Run(new PuffusForm());
    }
}
