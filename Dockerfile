FROM debian:12.11-slim

ARG PANDOC_VERSION=3.6.4
ARG MERMAID_CLI_VERSION=11.4.2

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates curl nodejs npm python3 python3-yaml chromium \
    latexmk texlive-xetex texlive-latex-extra texlive-fonts-recommended lmodern \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fsSLo /tmp/pandoc.deb \
    "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-amd64.deb" \
  && dpkg -i /tmp/pandoc.deb && rm /tmp/pandoc.deb \
  && npm install --global "@mermaid-js/mermaid-cli@${MERMAID_CLI_VERSION}" \
  && npm cache clean --force

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
WORKDIR /book
COPY . /book
RUN chmod +x scripts/build-book.sh scripts/preprocess.py
CMD ["scripts/build-book.sh"]

