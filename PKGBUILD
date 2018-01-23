# Maintainer: William Belanger <echo d2lsbGlhbS5iZWxyQGdtYWlsLmNvbQ== | base64 -d>

pkgname=qtpad
pkgdesc="Modern and customizable sticky note application"
url="https://github.com/willbelr/$pkgname"
pkgver=1.0
pkgrel=1
arch=('any')
license=('GPL3')
depends=('python>=3' 'python-pyqt5' 'qt5-svg' 'python-requests')
source=("${pkgname%-*}::git+https://github.com/willbelr/qtpad.git")
md5sums=('SKIP')

prepare()
{
  printf "#!/bin/bash\npython /usr/share/$pkgname/$pkgname.py \"\$@\"" > $pkgname"_exe"
}

package()
{
  install -Dm755 $pkgname"_exe" "$pkgdir/usr/bin/$pkgname"
  cd $pkgname
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
