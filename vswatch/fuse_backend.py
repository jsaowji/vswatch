####TODO: unused
###
###import os, stat, errno
###from typing import BinaryIO
#### pull in some spaghetti to make this stuff work without fuse-py being installed
###try:
###    import _find_fuse_parts
###except ImportError:
###    pass
###import fuse
###from fuse import Fuse
###
###
###if not hasattr(fuse, '__version__'):
###    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")
###
###fuse.fuse_python_api = (0, 2)
###
###
###class MyStat(fuse.Stat):
###    def __init__(self):
###        self.st_mode = 0
###        self.st_ino = 0
###        self.st_dev = 0
###        self.st_nlink = 0
###        self.st_uid = 0
###        self.st_gid = 0
###        self.st_size = 0
###        self.st_atime = 0
###        self.st_mtime = 0
###        self.st_ctime = 0
###
###class HelloFS(Fuse):
###    def __init__(self, *args, **kw):
###        Fuse.__init__(self,*args,**kw)
###        self.selection = "01"
###        self.script = "script.vpy"
###
###    def init_files(self,files):
###        self.files = files
###
###    def getattr(self, path):
###        st = MyStat()
###        if path == '/':
###            st.st_mode = stat.S_IFDIR | 0o755
###            st.st_nlink = 2
###            return st
###        for f in self.files:
###            if path == "/{}".format(f.name):
###                st.st_mode = stat.S_IFREG | 0o444
###                st.st_nlink = 1
###                st.st_size = f.full_file_len
###                return st
###        return -errno.ENOENT
###
###    def readdir(self, path, offset):
###        for r in  '.', '..':
###            yield fuse.Direntry(r)
###
###        for f in self.files:
###            yield fuse.Direntry(f.name)
###
###
###    def open(self, path, flags):
###        #TODO
###        #if path != hello_path_wav and path != hello_path_y4m:
###        #    return -errno.ENOENT
###        
###        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
###        if (flags & accmode) != os.O_RDONLY:
###            return -errno.EACCES
###
###    def read(self, path, size, offset):
###        for f in self.files:
###            if path == "/{}".format(f.name):
###                return f.read(offset,size)
###        return -errno.ENOENT
###def fuse_main():
###    usage=Fuse.fusage
###    server = HelloFS(version="%prog " + fuse.__version__,
###                     usage=usage,
###                     dash_s_do='setsingle')
###
###    server.parser.add_option(mountopt="script",    metavar="PATH", default='./script.vpy',help="scriptfile to use")
###    server.parser.add_option(mountopt="selection", metavar="SELECTION", default='01',help="argument for selection")
###
###    server.parse(values=server,errex=1)
###    server.init_vs_stuff()
###    if (server.fuse_args.modifiers["foreground"]):
###        import threading
###        import functools
###        import subprocess
###        import shlex
###        import time
###        def launch(mnt):
###            time.sleep(0.3)
###            #mnt = shlex.quote(mnt)
###
###            subprocess.Popen(["mpv",f"{mnt}/0.y4m", "--audio-file-auto=all","--chapters-file=/tmp/asd.chap"]).wait()
###            subprocess.Popen(["fusermount","-u",f"{mnt}"]).wait()
###        threading.Thread(target=functools.partial(launch,mnt=server.fuse_args.mountpoint)).start()
###
###    server.main()
