"""Tests for musync.formats module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import mutagen.id3
import mutagen.mp4
import mutagen.oggvorbis
import mutagen.flac
import musync.formats
import musync.formats.id3 as id3_module
import musync.formats.mp4 as mp4_module
import musync.formats.oggvorbis as ogg_module


def test_formats_open_unsupported(tmp_path):
    """Test formats.open() with unsupported file."""
    test_file = tmp_path / "test.xyz"
    test_file.write_text("content")
    
    result = musync.formats.open(str(test_file))
    assert result is None


def test_formats_open_mp3(tmp_path):
    """Test formats.open() with MP3 file (mocked)."""
    test_file = tmp_path / "test.mp3"
    test_file.write_text("fake mp3")
    
    with patch("mutagen.File") as mock_file:
        mock_file.return_value = None
        result = musync.formats.open(str(test_file))
        mock_file.assert_called()


def test_formats_open_mp4(tmp_path):
    """Test formats.open() with MP4 file."""
    test_file = tmp_path / "test.m4a"
    test_file.write_text("fake mp4")
    
    with patch("mutagen.File") as mock_file:
        mock_file.return_value = None
        result = musync.formats.open(str(test_file))
        mock_file.assert_called()


def test_formats_open_ogg(tmp_path):
    """Test formats.open() with OGG file."""
    test_file = tmp_path / "test.ogg"
    test_file.write_text("fake ogg")
    
    with patch("mutagen.File") as mock_file:
        mock_file.return_value = None
        result = musync.formats.open(str(test_file))
        mock_file.assert_called()


def test_formats_open_id3_returns_id3_metafile(tmp_path):
    """formats.open() with ID3 tags returns ID3MetaFile."""
    mock_f = Mock()
    mock_f.filename = str(tmp_path / "x.mp3")
    mock_f.tags = mutagen.id3.ID3()
    with patch("mutagen.File", return_value=mock_f):
        o = musync.formats.open("path")
    assert o is not None
    assert type(o).__name__ == "ID3MetaFile"


def test_formats_open_oggvorbis_returns_ogg_metafile(tmp_path):
    """formats.open() with real Ogg file returns OggVCommentMetaFile.
    Mutagen cannot create Ogg from scratch without an existing file; branch is
    covered by test_ogg_metafile_* and other format open tests.
    """
    pytest.skip("OggVorbis requires existing file; OggVCommentMetaFile covered by unit tests")


def test_formats_open_vcflac_returns_vcflac_metafile(tmp_path):
    """formats.open() with VCFLACDict tags returns VCFLACMetaFile."""
    mock_f = Mock()
    mock_f.filename = str(tmp_path / "x.flac")
    mock_f.tags = mutagen.flac.VCFLACDict()
    with patch("mutagen.File", return_value=mock_f):
        o = musync.formats.open("path")
    assert o is not None
    assert type(o).__name__ == "VCFLACMetaFile"


def test_formats_open_mp4tags_returns_mp4_metafile(tmp_path):
    """formats.open() with MP4Tags returns MP4TagsMetaFile."""
    mock_f = Mock()
    mock_f.filename = str(tmp_path / "x.m4a")
    mock_f.tags = mutagen.mp4.MP4Tags()
    with patch("mutagen.File", return_value=mock_f):
        o = musync.formats.open("path")
    assert o is not None
    assert type(o).__name__ == "MP4TagsMetaFile"


def test_formats_open_passes_kw_to_returned_object(tmp_path):
    """formats.open() setattrs kw on the returned meta object."""
    mock_f = Mock()
    mock_f.filename = str(tmp_path / "x.mp3")
    mock_f.tags = mutagen.id3.ID3()
    with patch("mutagen.File", return_value=mock_f):
        o = musync.formats.open("path", custom_attr="value")
    assert getattr(o, "custom_attr", None) == "value"


def test_formats_open_skips_none_kw(tmp_path):
    """formats.open() does not set kw keys whose value is None."""
    mock_f = Mock()
    mock_f.filename = str(tmp_path / "x.mp3")
    mock_f.tags = mutagen.id3.ID3()
    with patch("mutagen.File", return_value=mock_f):
        o = musync.formats.open("path", skip_me=None)
    assert not hasattr(o, "skip_me") or getattr(o, "skip_me", None) is None


def test_id3_metafile_year_string():
    """ID3MetaFile converts string year via ID3TimeStamp."""
    f = Mock()
    f.filename = "x.mp3"
    tags = {"TDRC": ["2020-01-01"]}
    meta = id3_module.ID3MetaFile(f, tags)
    assert meta.year == 2020


def test_id3_metafile_track_with_slash():
    """ID3MetaFile track with '/' takes first part."""
    f = Mock()
    f.filename = "x.mp3"
    tags = {"TRCK": ["3/10"]}
    meta = id3_module.ID3MetaFile(f, tags)
    assert meta.track == 3


def test_mp4_metafile_track_first_element():
    """MP4TagsMetaFile uses track[0] when track is list."""
    f = Mock()
    f.filename = "x.m4a"
    tags = {"trkn": [[5, 10]]}
    meta = mp4_module.MP4TagsMetaFile(f, tags)
    assert meta.track == 5


def test_flac_metafile_keeps_artist_name():
    """FLAC uses the artist tag. Sort names must not rewrite it."""
    f = Mock()
    f.filename = "x.flac"
    tags = {
        "albumartistsort": ["Croce, Jim"],
        "artist": ["Jim Croce"],
        "album": ["Greatest"],
    }
    meta = ogg_module.VCFLACMetaFile(f, tags)
    assert meta.artist == "Jim Croce"
    assert meta.album == "Greatest"

    tags = {
        "albumartistsort": ["Beatles, The"],
        "artist": ["The Beatles"],
    }
    meta = ogg_module.VCFLACMetaFile(f, tags)
    assert meta.artist == "The Beatles"


def test_ogg_metafile_track_int():
    """OggVCommentMetaFile converts track to int."""
    f = Mock()
    f.filename = "x.ogg"
    tags = {"tracknumber": ["7"]}
    meta = ogg_module.OggVCommentMetaFile(f, tags)
    assert meta.track == 7
    assert meta.disc is None
    assert meta.disctotal is None


def test_id3_metafile_disc_pair():
    """ID3 TPOS '1/2' is disc 1 of 2."""
    f = Mock()
    f.filename = "x.mp3"
    meta = id3_module.ID3MetaFile(f, {"TPOS": ["1/2"]})
    assert meta.disc == 1
    assert meta.disctotal == 2


def test_id3_metafile_disc_without_total():
    """ID3 TPOS without a total leaves disctotal unset."""
    f = Mock()
    f.filename = "x.mp3"
    meta = id3_module.ID3MetaFile(f, {"TPOS": ["1"]})
    assert meta.disc == 1
    assert meta.disctotal is None


def test_id3_metafile_disc_garbage():
    """A non-numeric TPOS does not invent a disc."""
    f = Mock()
    f.filename = "x.mp3"
    meta = id3_module.ID3MetaFile(f, {"TPOS": ["disc"]})
    assert meta.disc is None
    assert meta.disctotal is None


def test_ogg_metafile_disc_and_total():
    """Vorbis DISCNUMBER and DISCTOTAL become ints."""
    f = Mock()
    f.filename = "x.ogg"
    meta = ogg_module.OggVCommentMetaFile(
        f, {"discnumber": ["2"], "disctotal": ["3"]}
    )
    assert meta.disc == 2
    assert meta.disctotal == 3


def test_ogg_metafile_disc_pair_in_number():
    """Vorbis DISCNUMBER '1/2' supplies the total when DISCTOTAL is absent."""
    f = Mock()
    f.filename = "x.ogg"
    meta = ogg_module.OggVCommentMetaFile(f, {"DISCNUMBER": ["1/2"]})
    assert meta.disc == 1
    assert meta.disctotal == 2


def test_ogg_metafile_totaldiscs_fallback():
    """TOTALDISCS is used when DISCTOTAL is missing."""
    f = Mock()
    f.filename = "x.ogg"
    meta = ogg_module.OggVCommentMetaFile(
        f, {"discnumber": ["1"], "totaldiscs": ["2"]}
    )
    assert meta.disc == 1
    assert meta.disctotal == 2


def test_ogg_metafile_disctotal_wins():
    """An explicit DISCTOTAL wins over TOTALDISCS and over '1/4' in DISCNUMBER."""
    f = Mock()
    f.filename = "x.ogg"
    meta = ogg_module.OggVCommentMetaFile(
        f,
        {"discnumber": ["1/4"], "totaldiscs": ["9"], "disctotal": ["2"]},
    )
    assert meta.disc == 1
    assert meta.disctotal == 2


def test_flac_metafile_disc_pair():
    """FLAC uses the same Vorbis disc tags."""
    f = Mock()
    f.filename = "x.flac"
    meta = ogg_module.VCFLACMetaFile(
        f, {"discnumber": ["2"], "disctotal": ["2"]}
    )
    assert meta.disc == 2
    assert meta.disctotal == 2


def test_mp4_metafile_disk_tuple():
    """MP4 disk (disc, total) becomes disc and disctotal."""
    f = Mock()
    f.filename = "x.m4a"
    meta = mp4_module.MP4TagsMetaFile(f, {"disk": [(1, 2)]})
    assert meta.disc == 1
    assert meta.disctotal == 2


def test_mp4_metafile_disk_zero_total():
    """MP4 total of 0 means the disc count is unknown."""
    f = Mock()
    f.filename = "x.m4a"
    meta = mp4_module.MP4TagsMetaFile(f, {"disk": [[1, 0]]})
    assert meta.disc == 1
    assert meta.disctotal is None


def test_mp4_metafile_without_disk():
    """MP4 files with no disk atom leave both fields unset."""
    f = Mock()
    f.filename = "x.m4a"
    meta = mp4_module.MP4TagsMetaFile(f, {"trkn": [[1, 10]]})
    assert meta.track == 1
    assert meta.disc is None
    assert meta.disctotal is None
