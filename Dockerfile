FROM debian:12.11-slim

ARG PANDOC_VERSION=3.6.4

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates curl nodejs npm python3 python3-yaml python3-jsonschema chromium librsvg2-bin \
    latexmk texlive-xetex texlive-latex-extra texlive-latex-recommended texlive-fonts-recommended lmodern \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fsSLo /tmp/pandoc.deb \
    "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-amd64.deb" \
  && dpkg -i /tmp/pandoc.deb && rm /tmp/pandoc.deb

# Mermaid CLI's Puppeteer download is skipped; it drives the chromium
# package installed above instead (smaller image, one fewer download).
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /book
COPY package.json package-lock.json /book/
RUN npm ci
COPY . /book
RUN chmod +x scripts/build-book.sh

CMD ["scripts/build-book.sh"]
