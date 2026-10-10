"""Exclusive POSIX source publication. No cross-file recovery transaction."""
import os
from pathlib import Path
import stat
import uuid


class SourcePublicationError(OSError):
    def __init__(self,message,*,published,destination,candidate_key=None,registry_committed=False):
        super().__init__(message)
        self.published=published
        self.destination=str(destination)
        self.candidate_key=candidate_key
        self.registry_committed=registry_committed


class _Ops:
    open=staticmethod(os.open)
    write=staticmethod(os.write)
    fsync=staticmethod(os.fsync)
    close=staticmethod(os.close)
    link=staticmethod(os.link)
    unlink=staticmethod(os.unlink)
ops=_Ops()


def checkpoint(stage):
    """Test crash-cut seam, never a production recovery instruction."""


def _sync_directory(directory):
    if os.name!='posix' or not hasattr(os,'O_DIRECTORY'):
        raise OSError('POSIX directory sync unavailable')
    fd=ops.open(directory,os.O_RDONLY|os.O_DIRECTORY)
    try:ops.fsync(fd)
    finally:ops.close(fd)


def publish_source(destination,content,*,candidate_key=None):
    """Absent destination only, complete fsynced bytes become visible via link.

    On failure retains any published file and partial temp for inspection. Never
    adopts or overwrites. No safe link/fsync -> fail closed, no fallback.
    """
    if type(content) is not bytes:raise TypeError('exact source bytes required')
    path=Path(destination);temp=path.parent/f'.{path.name}.publish-{uuid.uuid4().hex}.tmp'
    fd=None;published=False
    try:
        if os.name!='posix' or not hasattr(os,'O_NOFOLLOW'):
            raise OSError('POSIX exclusive publication unavailable')
        try:path.lstat()
        except FileNotFoundError:pass
        else:raise FileExistsError('extension destination already exists; reconcile orphan')
        fd=ops.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        view=memoryview(content)
        while view:
            count=ops.write(fd,view)
            if count<=0:raise OSError('source write made no progress')
            view=view[count:]
        ops.fsync(fd);checkpoint('temp_fsynced')
        ops.close(fd);fd=None
        ops.link(temp,path);published=True;checkpoint('name_published')
        _sync_directory(path.parent);checkpoint('published_dir_fsynced')
        ops.unlink(temp);_sync_directory(path.parent);checkpoint('temp_removed_fsynced')
    except OSError as exc:
        raise SourcePublicationError('extension publication failed; inspect artifacts',
            published=published,destination=path,candidate_key=candidate_key) from exc
    finally:
        if fd is not None:ops.close(fd)
