# Maintainer: Milan <your-email@example.com>
pkgname=arch-backup-tool-git
_pkgname=arch-backup
pkgver=1.0.0.r0.g1234567
pkgrel=1
pkgdesc="PyQt6 GUI and CLI package baseline/dotfile tracking and recovery tool for Arch Linux & CachyOS"
arch=('any')
url="https://github.com/kosirm/arch-backup"
license=('MIT')
depends=('python' 'python-pyqt6' 'git' 'pacman' 'chezmoi')
makedepends=('git')
optdepends=(
  'konsave: KDE Plasma desktop configuration backup'
  'flatpak: Tracking installed flatpaks'
)
provides=('arch-backup-tool' 'cachyos-backup' 'cachyos-recovery')
conflicts=('arch-backup-tool' 'cachyos-backup' 'cachyos-recovery')
source=("git+${url}.git")
sha256sums=('SKIP')

pkgver() {
  cd "${srcdir}/${_pkgname}"
  git describe --long --tags 2>/dev/null | sed 's/\([^-]*-g\)/r\1/;s/-/./g' || printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
  cd "${srcdir}/${_pkgname}"
  
  # Run installer under fakeroot using DESTDIR and PREFIX=/usr
  PREFIX=/usr DESTDIR="${pkgdir}" ./install.sh
}
