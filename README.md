# Currently down!
A cloud outage took down a lot of the demo infrastructure. Rather than hacking together a fix, I'm cleaning up the backend and making it more robust. Once that's ready, this demo should work again.

# boorufeed_itl
`boorufeed_itl` is a module that scrapes boorus and provides the results to a `loop`.
All messages in a loop are *ephemeral*, so they're good for streaming uses, not
for robust dataset creation & maintenance.

>Note: I plan to update this repo to support robust dataset creation & maintence.

# Consuming scraped data
If you just want to consume data from [sources I'm already scraping](https://github.com/synthbot-anon/boorufeed_itl/tree/main/sample-configs), you can use the
[sample client](https://github.com/synthbot-anon/boorufeed_itl/blob/main/sample-client/client.py).
It's designed to be easily modifiable.

```bash
pip install --upgrade itllib
python3 sample-client/client.py
```

The `kwargs` will look like this:
```json
{
    "id": 2705431,
    "created_at": "2022-05-10T16:53:26.516Z",
    "tags": ["safe","solo","female","mare","pony","derpibooru import","earth pony","flower","color porn","lying down","roseluck","beautiful","rose","artist:ajvl","image","jpeg"],
    "format": "jpeg",
    "representations": {
        "full": "https://cdn.twibooru.org/img/2022/5/10/2705431/full.jpeg",
        "thumb": "https://cdn.twibooru.org/img/2022/5/10/2705431/thumb.webp"
    },
    "sha512_hash": "34bb2c7955050e5304aa93bd8b4faa43056fd57789299ca7099941433e65daedc4bd06f27fc02c87d15d405bd8a9741bce710ed5abf705b2be337a10b5f7d56c",
    "orig_sha512_hash": "34bb2c7955050e5304aa93bd8b4faa43056fd57789299ca7099941433e65daedc4bd06f27fc02c87d15d405bd8a9741bce710ed5abf705b2be337a10b5f7d56c"
}
```

# Running your own scraper
>**WARNING: This uses the cloud to host configuration files and pass messages.** \
I'm working on the local execution version. With the future local execution version, the steps will be the same, just with a slightly modified `loop_config.yaml` file. \
\
You don't need to configure anything special to use the cloud. These steps should just work.

First, start the scraper:
```bash
# Clone this repo and entry the directory
git clone https://github.com/synthbot-anon/boorufeed_itl
cd boorufeed_itl

# Install the depedencies and boorufeed_itl
pip install --upgrade .

# Create your own cluster, streams, and users
python3 -m loopctl apply loop_config.yaml

# Run the scraper. It will look for ./loop-resources and ./loop-secrets in the
# current directly. Both folders are created by the previous loopctl command.
python3 -m boorufeed_itl
```

Then, in a separate terminal, use [itlmon](https://github.com/ThatOneAI/itlmon) to apply the scraper configs. In Windows, you'll need to use powershell
for this step since `itlmon` doesn't run in git-bash.
```bash
# Install itlmon
pip install --upgrade itlmon

# Start itlmon. By default, it checks ./loop-resources/ and ./loop-secrets/ for cluster, stream, and user info. Both folders were created by loopctl above.
python3 -m itlmon --client op

# Apply the configs inside the terminal UI that pops up
/cluster boorufeed-configs apply ./sample-configs/
```

You can close `itlmon` at any time with:
```bash
/quit
```

The scraper will continue running even if you close `itlmon`.

# Reading messages from your own scraper
Once the scraper is running, you can use `itlmon` to see messages being passed around by clicking
on stream names on the side. It will only scrape *new* images, and it will only check for
new images once every (by default) 10 minutes. You'll see messages in the `debug` stream
immediately, but you won't see messages in the booru streams until it checks for new images.

The scraper keeps track of the last images it's seen. So if you stop `boorufeed_itl` for an
hour then re-run it, it will know to look for and send all new images from the previous hour.

You can use this modified `client.py` script to access the messages from your own scrapes programmatically:
```python
from itllib import Itl

itl = Itl("./loop-resources")
itl.start()

@itl.ondata("twibooru")
async def on_twibooru_img(*args, **kwargs):
	print('twibooru image:', args, kwargs)

@itl.ondata("derpibooru")
async def on_derpibooru_img(*args, **kwargs):
	print('derpibooru image:', args, kwargs)

@itl.ondata("ponybooru")
async def on_ponybooru_img(*args, **kwargs):
	print('ponybooru image:', args, kwargs)


itl.wait()
```

# How does it work
TODO
