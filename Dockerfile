# syntax = docker/dockerfile:1.3
ARG TAG=latest

FROM golang:alpine AS build
RUN go install github.com/mccutchen/go-httpbin/v2/cmd/go-httpbin@${TAG}

FROM gcr.io/distroless/static
COPY --from=build /go/bin/go-httpbin /

EXPOSE 8080
CMD ["/go-httpbin"]