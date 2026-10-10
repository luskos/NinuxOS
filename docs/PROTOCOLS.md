# The protocols of NinuxOS - first writing (v3.0.11)

What two programs must agree on to pass messages, pictures, video and files to each other, when
all they share is a handle. Programs are different (my messenger, your "lessenger"); the protocol
is one. No platform, no server that owns the talk, no browser.

This is a first writing by Claude from the owner's words (TODO.md, part 4d). Nothing of it is
in code yet. Every "open" below is a question for the owner; the rest is a proposal to be
corrected. It is built only from what the system already has: ASMO objects, Ed25519 signatures
and SHA-256 (the kernel has both), the identity of a machine (`whoami`), Meta Net of the suit
k_net, and the call of a named socket of another object (the system's table, +0x80).

## 1. One rule: what travels is an ASMO object

A message, a picture, a file - each travels as an ordinary object: DATA + META. Nothing new has
to be invented for storing, showing, checking or keeping it: `view` shows it, the cabinet keeps
it, the Sentinel's kind of check applies to it. A program that knows nothing about a kind of
message can still keep it and show its META.

The envelope is the META of the object:

| key | what | example |
|---|---|---|
| `type` | always `parcel` | `parcel` |
| `proto` | the protocol and its version | `nx.msg/1` |
| `from` | the handle of the sender | `luskos@7f3a91c2` |
| `to` | the handle of the receiver, or of a group | `mira@0b55e410` |
| `id` | the number of this parcel: the first 16 hex letters of the SHA-256 of its DATA and the META lines above the signature | `9c41...` |
| `re` | the `id` this one answers or continues (may be missing) | |
| `time` | seconds since 2000-01-01, by the sender's clock | `845210000` |
| `kind` | what the DATA are (the table of part 3) | `text` |
| `part` | for something sent in pieces: `n/of` | `3/12` |
| `sig` | Ed25519 signature of everything above, by the sender's key, in hex | |

The DATA are the content itself, as it is - the letters of the text, the bytes of the picture.

## 2. A handle

`name@machine`: the name a person chose, and the first 8 hex letters of the identity of the
machine the handle was made on (the ID `whoami` shows). With the handle goes a public key
(Ed25519); the secret half stays in the person's own objects. Two people "know each other's
handle" when each holds the other's handle and public key - passed by hand (a stick, a QR
picture as Support already shows) or over the network once.

- Open: one key a person, carried from machine to machine, or one key a machine?
- Open: where the list of known handles lives (an object `people`? Socials keeps it?).

## 3. The kinds (`proto` and `kind`)

| proto | kind | DATA | notes |
|---|---|---|---|
| `nx.msg/1` | `text` | the text, Windows-1251 today, UTF-8 when the system has Unicode (a META line `charset` says which) | |
| `nx.msg/1` | `seen` | empty | `re` names the message that was read |
| `nx.pic/1` | `image` | the picture as the system keeps pictures (width, height, dots); later PNG | one parcel if it fits, else pieces |
| `nx.file/1` | `object` | a whole ASMO object, header to trailer | this is how a program is given to someone: no installing |
| `nx.file/1` | `piece` | a piece of a bigger DATA | `part` = `n/of`, `re` = the `id` of the first piece; the last piece carries `sha` = the SHA-256 of the whole |
| `nx.video/1` | `frame` | one frame or a run of frames | pieces in order; a lost piece is skipped, not asked for again |
| `nx.video/1` | `sound` | a run of samples | as above |
| `nx.who/1` | `hello` | the sender's public key | the first parcel between two handles |
| `nx.who/1` | `here` | empty | "I am reachable now"; sent to those who hold my handle |

A program answers a `proto` it does not know with nothing; one it knows in an older version, in
that version. New kinds are added by adding rows, never by changing a row.

## 4. How a parcel gets there

Three ways, the same parcel in each:

1. **On the same machine**: from program to program through a relay - the sender calls the
   socket `take` of the relay object with the parcel; the relay calls `take` of the receiver.
   (No program reaches into another: DIRECTIVE.md.)
2. **Between two machines that see each other**: over Meta Net (k_net), which already signs and
   encrypts what it carries. A parcel is one Meta Net page, or several for pieces.
3. **Between machines that do not**: carried - on a stick (`share`, `send`, `get` exist), or
   left with a machine of NET that both reach, which keeps it until asked. Such a machine keeps
   parcels it cannot read: the DATA are encrypted for the receiver (part 5).

4. **Over a cable between two machines** (the owner, 11 October 2026: USB-C, "check-mate"):
   the two take turns - one sends while the other takes, then they change places - and a
   relay keeps count of whose turn it is. Needs a port on each machine that can be either
   end of a USB link, or Thunderbolt / USB4 (TODO.md, part 4f).

- Open: how a handle is turned into "where that machine is now" - this is the chain of machines
  (TODO.md, the order of work, 32). Until then: the address is typed, or found on the local net.

## 5. Closed to others

The DATA of a parcel are encrypted for the receiver, the META stay readable (so that a machine
that carries it knows where to). Proposal: X25519 from the two Ed25519 keys for a shared secret,
ChaCha20 for the DATA - both are small enough to write in PyTon or in a suit. A META line
`crypt:x25519-chacha20` says so; without the line the DATA are open.

- Open: is the META too much to leave readable (who talks to whom)? The alternative is a second,
  outer envelope with only `to`.

## 6. What a program must do to speak it

- keep its handle and key; answer `nx.who/1`;
- have a socket `take(parcel)`: check `sig`, then act on `proto` and `kind`, or keep the object;
- send by calling the relay's `take`.

Socials (apps/Socials.asmo, empty today) is to be the first such program; any other is as good.

## 7. What has to exist first

| needed | where it stands |
|---|---|
| the call of another object's socket from PyTon (`+0x80`) | the place is known (v3.0.11), not connected in py2asm |
| programs that live on while not on the screen (a relay must be there) | TODO.md, order of work 14 |
| signing and checking from a program (the kernel has Ed25519 and SHA-256 for itself) | no place in the system's table for it yet |
| the network functions for programs (`net_ask` ...) | TODO.md, order of work 11 |
| X25519 and ChaCha20 | not written |
