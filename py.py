files = [{'type': 'image/jpg','name': 'image.jpg', 'size':10}, {'type': 'audio/jpg','name': 'd.mp3', 'size':10}, {'type': 'ddd/jpg', 'name': 'image.doc', 'size':10}, {'type': 'video/jpg', 'name': 'image.doc', 'size':10}]


ext_list = [
    {
    'audio_ext': ['audio']
    },
    {
    'videos_ext': ['video']
    },
    {
    'docs_ext': ['pdf','doc','docx','xls','ppt','txt']
    },
    {
    'images_ext': ['image']
    }
]

name = '/2021-09-13_19.32.54-modified_7h8vJta.png'
print(name.split('.')[-1])
