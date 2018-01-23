# Maintainer: William Belanger <echo d2lsbGlhbS5iZWxyQGdtYWlsLmNvbQ== | base64 -d>
# PKGBUILD is broken, please use 'makepkg --skipchecksums' for now

pkgname=qtpad
pkgdesc="Modern and customizable sticky note application"
url="https://github.com/willbelr/$pkgname"
pkgver=1.0
pkgrel=1
arch=('any')
license=('GPL3')
source=('https://github.com/willbelr/qtpad/archive/master.zip')
depends=('python>=3' 'python-pyqt5' 'qt5-svg' 'python-requests')
md5sums=('dcabf47186ffaccd6b8d9a6f2a308c22')

prepare()
{
  printf "#!/bin/bash\npython /usr/share/$pkgname/$pkgname.py \"\$@\"" > $pkgname
}

package()
{
  install -Dm755 $pkgname "$pkgdir/usr/bin/$pkgname"
  cd $pkgname"-master"
  install -Dm755 $pkgname.desktop "$pkgdir/usr/share/applications/$pkgname.desktop"
  install -Dm755 $pkgname.py "$pkgdir/usr/share/$pkgname/$pkgname.py"
  install -Dm644 gui_child.ui "$pkgdir/usr/share/$pkgname/gui_child.ui"
  install -Dm644 gui_profile.ui "$pkgdir/usr/share/$pkgname/gui_profile.ui"
  install -Dm644 gui_preferences.ui "$pkgdir/usr/share/$pkgname/gui_preferences.ui"
  for file in icons/* ; do
      install -Dm644 $file $pkgdir/usr/share/$pkgname/$file
  done
  install -Dm644 README.md "$pkgdir/usr/share/$pkgname/README.md"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
