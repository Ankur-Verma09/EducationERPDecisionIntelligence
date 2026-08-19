FROM golang:1.25.7-alpine AS gosu-builder

RUN CGO_ENABLED=0 go install github.com/tianon/gosu@1.17

FROM postgres:16-alpine

COPY --from=gosu-builder /go/bin/gosu /usr/local/bin/gosu
COPY docker/postgres/init/001-runtime-role.sql /docker-entrypoint-initdb.d/001-runtime-role.sql
