import mutagen.id3
import mutagen.oggvorbis

from . import meta


class OggVCommentMetaFile(meta.MetaFile):
    __translate__ = {
        "album": "album",
        "date": "year",
        "tracknumber": "track",
        "discnumber": "disc",
        "disctotal": "disctotal",
        "totaldiscs": "disctotal",
        "artist": "artist",
        "title": "title",
    }

    def __init__(self, f, tags):
        meta.MetaFile.__init__(self, f, tags)

        if self.track:
            self.track = int(self.track)

        if self.year:
            self.year = mutagen.id3.ID3TimeStamp(self.year).year


class VCFLACMetaFile(meta.MetaFile):
    __translate__ = {
        "album": "album",
        "date": "year",
        "tracknumber": "track",
        "discnumber": "disc",
        "disctotal": "disctotal",
        "totaldiscs": "disctotal",
        "artist": "artist",
        "title": "title",
    }

    def __init__(self, f, tags):
        meta.MetaFile.__init__(self, f, tags)

        if self.track:
            self.track = int(self.track)

        if self.year:
            self.year = mutagen.id3.ID3TimeStamp(self.year).year
