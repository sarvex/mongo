# Dockerfile
# First image to build the binary
FROM alpine@sha256:77726ef6b57ddf65bb551896826ec38bc3e53f75cdde31354fbffb4f25238ebd as builder

RUN apk --no-cache add make gcc libc-dev
COPY . /src
RUN mkdir /pkg && cd /src && make && make DESTDIR=/pkg install

# Second minimal image to only keep the built binary
FROM alpine@sha256:77726ef6b57ddf65bb551896826ec38bc3e53f75cdde31354fbffb4f25238ebd

# Copy the built files
COPY --from=builder /pkg /

# Copy the license as well
RUN mkdir -p /usr/local/share/licenses/zstd
COPY --from=builder /src/LICENSE /usr/local/share/licences/zstd/

# Just run `zstd` if no other command is given
CMD ["/usr/local/bin/zstd"]
