Evolve Music 2
====================

Overview
---------------------
Automatically generate music using python.

Documentation
---------------------

## Installation

So, you want to have your computer make music for you, huh?  Came to the right spot.  Follow these simple instructions, and we'll get you up and running in no time.  This has only been fully tested on OSX.  It should work on Linux with some modifications, but no guarantees.

1.  Clone this repo with `git clone https://github.com/VikParuchuri/evolve-music2.git`.
2.  Switch to the repo folder with `cd evolve-music2`.
3.  Install the system packages in `brew-packages.txt` (osx) or `apt-packages.txt` (linux).
    * If osx, `brew install INSERT_PACKAGENAME_HERE`.
    * If linux, `apt-get install INSERT_PACKAGENAME_HERE`.
    * `apt-packages.txt` may not be comprehensive, so if you get any missing dependency errors, you may need to revisit this.
4.  Install the python pre-requirements with `pip install -r pre-requirements.txt` -- scipy doesn't like when numpy isn't already installed.  [Virtualenv](https://virtualenv.pypa.io/en/latest/) recommended.
5.  Install the python packages using `pip install -r requirements.txt`.  [Virtualenv](https://virtualenv.pypa.io/en/latest/) recommended.
    * Installing the `cryptography` package on OSX is a pain -- if you get any errors, verify that you have the `openssl` system package properly installed, and do `brew update` and `brew upgrade`.  Running `env ARCHFLAGS="-arch x86_64 -Wno-error=unused-command-line-argument-hard-error-in-future" LDFLAGS="-L/usr/local/opt/openssl/lib" CFLAGS="-I/usr/local/opt/openssl/include" pip install cryptography==0.5.4` can also help.
6.  Download a soundfont, used to render midi.  I got mine [here](http://www.schristiancollins.com/soundfonts/GeneralUser_GS_1.44-FluidSynth.zip).
    * Put the `.sf2` file in `data/soundfont`.
    * Update `SOUNDFONT_PATH` in `settings.py` to point to your soundfont.
    
## Usage

1.  Run the scrapy crawler
    * Use `cd crawler/crawler` to go into the crawler directory.
    * Run `scrapy crawl mas` to crawl one site.
    * Run `scrapy crawl mws` to crawl another site.
    * You should now have `.mid` files in `data/midi/full`, and a file at `data/full.json`.
    * It's possible that one or more of the .mid files are just text stored as `.mid`, and you may get errors later (but you'll be able to delete them then).
    * Switch back to the `evolve-music2` directory (project root).
2.  You can now run `python evolve_tracks.py` to evolve tracks.
    * You can pass two optional arguments, the number of tracks, and the number of evolutions.  `python evolve_tracks.py 20 5` will make 20 tracks total, and run through 5 evolutions.
    * The generated music will be in `data/good`.  Both midi and ogg files will be available.  You'll see as many files as there were evolutions.
    * If you get any errors while running this command, or if it hangs for over 30 minutes, you should check the logs at `data/em.log`. If the last line mentions a midi or ogg file, you should delete it -- it's probably corrupt.
    * All the features for the training data are extracted the first time, so the command will be much faster the second time you run it and beyond.  If you need to regenerate training features, delete `data/generated/train_features.csv`.
    * If you set evolutions high (above 3 or 4), you'll see some duplicate tracks -- this is because the "best" track stays the "best" through multiple generations.
    
Contributions
---------------------

Are great.  Submit a pull request if you have any.