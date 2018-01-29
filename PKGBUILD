# Maintainer: William Belanger <echo d2lsbGlhbS5iZWxyQGdtYWlsLmNvbQ== | base64 -d>

pkgname=qtpad
pkgdesc="Modern and customizable sticky note application"
url="https://github.com/willbelr/$pkgname"
pkgver=1.0.0
pkgrel=1
arch=('any')
license=('GPL3')
depends=('python>=3' 'python-pyqt5' 'qt5-svg' 'python-requests')
source=("${pkgname%-*}::git+https://github.com/willbelr/qtpad.git")
md5sums=('SKIP')

package()
{
  cd "$pkgname"
  python setup.py install --root="$pkgdir"
}
