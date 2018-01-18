# Maintainer: William Belanger <echo d2lsbGlhbS5iZWxyQGdtYWlsLmNvbQ== | base64 -d>
pkgname=qtpad
pkgdesc="Modern and customizable sticky note application"
url="https://github.com/willbelr/$pkgname"
_gitroot="https://github.com/willbelr/qtpad.git"
_gitname="$pkgname"
pkgver=1.0
pkgrel=1
arch=('any')
license=('GPL3')
depends=('python>=3' 'python-pyqt5' 'qt5-svg' 'python-requests')
makedepends=('git')

build()
{
  cd ${srcdir}/
  if [[ -d ${_gitname} ]]; then
      rm -rf ${_gitname}
      msg "Cleaned old git directory"
  fi
  msg "Connecting to the git server"
  git clone ${_gitroot}
  msg "git repository successfully cloned"
}

package()
{
  msg "Copying program files"
  cd "$pkgname"
  install -Dm755 qtpad.py "$pkgdir/usr/share/$pkgname/$pkgname.py"
  install -Dm644 gui_child.ui "$pkgdir/usr/share/$pkgname/gui_child.ui"
  install -Dm644 gui_profile.ui "$pkgdir/usr/share/$pkgname/gui_profile.ui"
  install -Dm644 gui_preferences.ui "$pkgdir/usr/share/$pkgname/gui_preferences.ui"
  for file in icons/* ; do
      install -Dm644 $file $pkgdir/usr/share/$pkgname/$file
  done
  install -Dm644 README.md "$pkgdir/usr/share/$pkgname/README.md"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

  msg "Creation of a system shortcut"
  echo -e "#!/bin/bash
python /usr/share/$pkgname/$pkgname.py \"\$@\"" > $pkgname
  install -Dm755 $pkgname "$pkgdir/usr/bin/$pkgname"

  msg "Creation of a desktop file"
  echo -e "[Desktop Entry]
Name=$pkgname
Exec=$pkgname
Terminal=false
Type=Application
Icon=view-compact-symbolic
NoDisplay=true" > $pkgname.desktop
  install -Dm755 $pkgname.desktop "$pkgdir/usr/share/applications/$pkgname.desktop"

  if [[ `ps 1 | grep systemd` ]]; then
    msg "Creation of a systemd service"
    echo -e "[Unit]
Description=qtpad
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python /usr/share/$pkgname/$pkgname.py

[Install]
WantedBy=multi-user.target" > $pkgname.service
    install -Dm644 $pkgname.service "$pkgdir/lib/systemd/system/$pkgname.service"
  fi
  msg "Done. Thank you."
  msg "Please enable '$pkgname' systemd service to launch application on startup"
}
