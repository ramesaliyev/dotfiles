FROM ubuntu:24.04

RUN apt-get update

# Locale setup — Ubuntu images ship with no locale configured (LANG=C/POSIX by default).
# Without UTF-8, multi-byte Unicode characters (e.g. tmux-powerline glyphs) render as underscores.
RUN apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Core utilities
RUN apt-get install -y sudo curl git

# Editor
RUN apt-get install -y vim

# Python
RUN apt-get install -y python3 python3-pip python3-venv
