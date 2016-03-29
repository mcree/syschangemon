# coding: utf-8
# Copyright (c) 2015 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


from __future__ import print_function
from __future__ import unicode_literals
import hashlib
import codecs


class BoundsError(Exception):

    def __init__(self, size, length, offset):
        msg = ("Bounds error! length (%s), offset (%s) must be >= 0"
               " and length + offset (%s) <= size (%s).")
        args = (length, offset, length + offset, size)
        Exception.__init__(self, msg % args)


def _file_size(obj):
    obj.seek(0, 2)
    return obj.tell()


def _as_chunks(length, limit):
    return [limit] * (length // limit) + [length % limit]


def _is_filepath(path):
    return type(path) in [type(b'bytes'), type('str')]


def _bytes_to_int(data):
    if len(data) == 0:
        return 0
    return int(codecs.encode(data, 'hex_codec'), 16)


def compute_from_obj(obj, offset=0, length=0, seed=b"",
                     hash_algorithm=hashlib.sha256):

    # check input
    assert(isinstance(seed, bytes))
    size = _file_size(obj)
    length = length if length else size - offset
    if length < 0 or offset < 0 or length + offset > size:
        raise BoundsError(size, length, offset)

    # start reading from offset
    obj.seek(offset)

    # add seed if given
    hasher = hash_algorithm()
    if seed:
        hasher.update(seed)

    # hash data
    chunks = _as_chunks(length, 1024 * 1024)  # 1M chunks for low RAM machines
    for chunk_size in chunks:
        buf = obj.read(chunk_size)
        hasher.update(buf)
    return hasher.digest()


def sample_from_obj(obj, sample_size, sample_count=1, seed=b"",
                    hash_algorithm=hashlib.sha256):

    # check input
    assert(sample_size > 0 and sample_count > 0)
    assert(isinstance(seed, bytes))

    # split into chunks of sample_size or less
    # always at least on chunk, possibly of size 0
    chunks = _as_chunks(_file_size(obj), sample_size)

    # hash chunks from pool and remove already hashed to spread evenly
    chunks_pool = list(enumerate(chunks[:]))  # enumerate to remember position
    for index_not_used in range(sample_count):

        # refill poll when empty
        if len(chunks_pool) == 0:
            chunks_pool = list(enumerate(chunks[:]))

        # hash chunk
        chunk_index = _bytes_to_int(seed) % len(chunks_pool)  # index from seed
        chunk_position, length = chunks_pool[chunk_index]
        offset = chunk_position * sample_size
        digest = compute_from_obj(obj, offset=offset, length=length, seed=seed,
                                  hash_algorithm=hash_algorithm)

        seed = digest  # use digest as next seed
        del chunks_pool[chunk_index]  # remove chunk from pool
    return digest  # return last digest


def compute_from_path(path, *args, **kwargs):
    with open(path, 'rb') as obj:
        return compute_from_obj(obj, *args, **kwargs)


def compute(f, *args, **kwargs):
    if _is_filepath(f):
        return compute_from_path(f, *args, **kwargs)
    return compute_from_obj(f, *args, **kwargs)


def sample_from_path(path, *args, **kwargs):
    with open(path, 'rb') as obj:
        return sample_from_obj(obj, *args, **kwargs)


def sample(f, *args, **kwargs):
    if _is_filepath(f):
        return sample_from_path(f, *args, **kwargs)
    return sample_from_obj(f, *args, **kwargs)
