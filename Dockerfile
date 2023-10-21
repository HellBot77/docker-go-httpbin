# syntax = docker/dockerfile:1.3
FROM golang:alpine AS build

RUN go install github.com/mccutchen/go-httpbin/v2/cmd/go-httpbin@latest

FROM gcr.io/distroless/static

COPY --from=build /go/bin/go-httpbin /

EXPOSE 8080
CMD ["/go-httpbin"]