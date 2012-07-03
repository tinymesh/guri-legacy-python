from distutils.core import setup
setup(name='guri',
      version='1.0',
      py_modules=['guri'],
      requires = ["serial", "binascii"],
      author="Olav Frengstad",
      author_email="olav@tiny-mesh.com",
      description="Simple serial to TCP/IP communications for TinyMesh devices",
      )
