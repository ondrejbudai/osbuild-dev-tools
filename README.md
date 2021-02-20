Preparing a release in the Fedora dist-git:
```
./prepare-release.py \
  --package osbuild-composer \
  --url https://github.com/osbuild/osbuild-composer/ \
  --distgit ssh://obudai@pkgs.fedoraproject.org/rpms/osbuild-composer.git \
  --version 27 \
  --author "Ondrej Budai <obudai@redhat.com>" \
  --release f32 \
  --pkgtool fedpkg
```
