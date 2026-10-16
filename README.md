NinuxOS v3.2.34, sealed, in 18 part(s).

    copy /b NinuxOS.bundle.gpg.001 + NinuxOS.bundle.gpg.002 NinuxOS.bundle.gpg     (Windows; all the parts, in order)
    cat NinuxOS.bundle.gpg.* > NinuxOS.bundle.gpg                                 (elsewhere)
    gpg -d -o NinuxOS.bundle NinuxOS.bundle.gpg
    git clone NinuxOS.bundle NinuxOS_v3
