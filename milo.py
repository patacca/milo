#!/bin/env python3

import json, requests, sys, os
from PIL import Image


def usage():
	print(f'Usage: {sys.argv[0]} URL')

if __name__ == '__main__':
	if len(sys.argv) != 2:
		usage()
		exit(1)

	url = sys.argv[1]
	r = requests.get(url)
	if not r.ok:
		print(f'HTTP {r.status_code} returned')
		exit(1)

	manifest = json.loads(r.text)
	title = manifest['label']
	imagesUrl = [manifest['sequences'][0]['canvases'][k]['images'][0]['resource']['service']['@id'] for k in range(len(manifest['sequences'][0]['canvases']))]
	
	if not os.path.isdir('output'):
		os.mkdir('output')
	if not os.path.isdir(f'output/{title}'):
		os.mkdir(f'output/{title}')

	print(f'Downloading {len(imagesUrl)} files ...')
	count = 0
	images = []
	for i in imagesUrl:
		print(f'{count} ',)
		realUrl = i + '/full/full/0/native.jpg'
		r = requests.get(realUrl)
		if not r.ok:
			print(f'url {realUrl} returned HTTP {r.status_code}')
			exit(1)
		
		f = open(f'output/{title}/{count}.jpg', 'wb')
		f.write(r.content)
		f.close()

		images.append(Image.open(f'output/{title}/{count}.jpg'))
		images[-1].convert('RGB')
		
		count += 1

	if len(images) > 0:
		images[0].save(f'output/{title}/{title}.pdf', save_all=True, append_images=images[1:])

	print('Done')
