#
# Musync meta - used to handle music-files metadata.
#
# author: John-John Tedro
# version: 2008.1
# Copyright (C) 2007 Albin Stjerna, John-John Tedro
#
#    This file is part of Musync.
#
#    Musync is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Musync is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Musync.  If not, see <http://www.gnu.org/licenses/>.

#imports
import musync.printer as Printer;
import traceback;

#partials
from mutagen import flac, oggvorbis, easyid3
from mutagen.mp3 import MP3
from musync.errors import WarningException, FatalException;
from musync.opts import Settings;
from musync.subp import sanitize_with_filter;

# 
#
#
#
#

def openaudio(p):
    """
    Opens audiofiles in an attempt to read their metadata.
    @param p musync.commons.Path object describing the file.
    @throws WarningException when file-extension of p is unsupported.
    """
    audio = None;

    #check before to simplify exception throwing.
    #these are the hardcoded extensions that mutagen supports.
    if p.ext not in ["flac","ogg","mp3"]:
        raise WarningException( "unknown extension '%s' - %s"%(p.ext, p.path) );

    try:
        if ( p.ext == "flac" ):
            audio = flac.FLAC(p.path);
        elif ( p.ext == "ogg" ):
            audio = oggvorbis.Open(p.path)
        elif ( p.ext == "mp3" ):
            # fix some sort of sanity check here.
            audio = MP3(p.path, ID3=easyid3.EasyID3);
    except Exception,e:
        Printer.log(p.path + ":\n" + traceback.format_exc() );
        raise FatalException("mutagen crashed");

    #this is not good.
    if audio.tags is None:
        raise FatalException("file contains no metadata");
    
    if len(audio) is 0:
        raise FatalException("file contains blank metadata");
    
    return audio;

def readmeta(p):
    """
    Makes an attempt to read metadata from a file.
    @param p musync.commons.Path object describing the file.
    """

    meta={"album":None, "artist":None, "title":None, "track":None};
    audio = openaudio(p);
   
    for key in audio.keys():
        to_key = key;
        from_key = key;
        # corrections go here
        if key == "tracknumber":
            to_key = "track";

        # these are the keys that we can use
        if to_key not in ["artist","album","title","track"]:
            continue;

        # try to read from file.
        try:
            meta[to_key] = audio[from_key][0];
        except Exception,e:
            raise FatalException("metadata corrupt - %s"%(p.path));

    # apply modifications
    for k in Settings["modify"]:
        if Settings["modify"][k]:
            meta[k] = Settings["modify"][k];
    
    for field in ["album", "artist", "title", "track"]:
        if meta[field] is None:
            if Settings["no-fixme"]:
                meta[field] = unicode("");
            else:
                Printer.fixlog(p.path, meta);
                raise WarningException("fixme - %s"%(p.path));

    return meta;

def cleanmeta(meta):
    """
    Cleans up metadata and makes it ready for expansion.
    @param meta Dictionary containing all metadata keys.
    """
    
    try:
        track = meta["track"];
        #some tags like to be track/#of tracks, take care of them here
        if track.find('/') > -1:
            meta["track"] = int(
                track[ 0 : track.find('/') ]
            );
        else:
            meta["track"] = int(track);
    except Exception,e:
        raise FatalException("cannot use tracknumber");
    # no plan for this section yet, keep along...
    #sanitize all strings
    for key in ["artist","album","title"]:
        meta[key] = sanitize_with_filter(meta[key], key);
        # FIXME: clean meta
        #meta[key] = "cleaned!";
    return meta;

