# BitTorrent

A simple BitTorrent client using Python 3.10. The current implementation only works for downloading single files.


## Install dependencies

This project uses Python version 3.10 and depends on the **tqdm** library for printing progress bars to the console

```~shell
sudo apt install python3.10
pip install tqdm
```


## How to execute

To execute the program use the Python interpreter and give it the path to a torrent file and optionally a path to an output directory

```~shell
python3.10 src/main.py path/to/file.torrent [path/to/output/directory/]
```


## Features

- [x] Single file download
- [ ] Multi-file download
- [ ] Resume download
- [ ] Uploading files


## References

- [BitTorrent reference](https://www.bittorrent.org/beps/bep_0052.html)
- [A BitTorrent client in Python 3.5](https://markuseliasson.se/article/bittorrent-in-python/)
- [Building a BitTorrent client from the ground up in Go](https://blog.jse.li/posts/torrent/)
