from itllib import Itl

itl = Itl("https://gist.github.com/synthbot-anon/299308e34d5e2619b10cf688c64e3f9d")
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
