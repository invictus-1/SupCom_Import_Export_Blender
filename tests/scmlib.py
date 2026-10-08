"""Minimal independent SCM/SCA readers for round-trip checks (format per GPG's layout; little-endian)."""
import struct


def cstrings(b):
    return [x.decode('ascii', 'replace') for x in b.split(b'\0')[:-1]]


def read_scm(path):
    d = open(path, 'rb').read()
    (marker, ver, boneoff, wbones, vertoff, xvoff, vcount, idxoff, icount, infooff, infosize, tbones) = \
        struct.unpack_from('<4s11I', d, 0)
    assert marker == b'MODL', marker
    bones = []
    for i in range(tbones):
        r = struct.unpack_from('<16f3f4f4i', d, boneoff + i * 108)
        name_off = r[23]
        name = d[name_off:d.index(b'\0', name_off)].decode('ascii', 'replace')
        bones.append(dict(name=name, rpi=r[0:16], pos=r[16:19], rot=r[19:23], parent=r[24]))
    verts = []
    for i in range(vcount):
        r = struct.unpack_from('<3f3f3f3f2f2f4B', d, vertoff + i * 68)
        verts.append(dict(pos=r[0:3], nrm=r[3:6], tan=r[6:9], bin=r[9:12], uv=r[12:14], uv2=r[14:16], bone=r[16]))
    tris = [struct.unpack_from('<3H', d, idxoff + i * 6) for i in range(icount // 3)]
    info = cstrings(d[infooff:infooff + infosize]) if infosize else []
    return dict(version=ver, weighted=wbones, bones=bones, verts=verts, tris=tris, info=info)


def read_sca(path):
    d = open(path, 'rb').read()
    magic, ver, nframes, duration, nbones, nameoff, linkoff, animoff, framesize = struct.unpack_from('<4siifiiiii', d, 0)
    assert magic == b'ANIM'
    names = cstrings(d[nameoff:linkoff])[:nbones]
    links = struct.unpack_from('<%di' % nbones, d, linkoff)
    root = struct.unpack_from('<3f4f', d, animoff)
    frames = []
    off = animoff + 28
    for f in range(nframes):
        t, flags = struct.unpack_from('<fi', d, off); off += 8
        bones = [struct.unpack_from('<3f4f', d, off + b * 28) for b in range(nbones)]
        off += 28 * nbones
        frames.append(dict(t=t, flags=flags, bones=bones))
    return dict(version=ver, duration=duration, names=names, links=links, root=root, frames=frames)
