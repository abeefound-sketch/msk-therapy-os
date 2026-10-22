# Hugging Face Docker Space Deployment (synthetic demonstration only)

**Status:** Docker recipe created; *not built with Docker or deployed to Hugging Face* in this environment. **Do not supply a token until verified build and repository upload are needed.**

## Configure the Space

The root `README.md` contains Hugging Face YAML: `sdk: docker`, `app_port: 7860`. `Dockerfile` uses Python 3.12 stdlib and runs `deploy/start-space.sh`. Public Docker defaults to `MSK_PUBLIC_DEMO_READONLY=1`, disallowing all state-changing API routes, except the stateless rule-based safety drill (`/api/screen-safety`). Login and data editing are intentionally disabled. The demo DB is synthetic and disposable.

**Never expose a writable non-demo instance.** The inherited application has intentionally seeded demo logins and several legacy endpoints that assume localhost. It is **not** an Internet-ready clinical backend.

## Local test before authenticated deployment

```bash
docker build -t msk-therapy-os-demo .
docker run --rm -p 7860:7860 -e PORT=7860 -e MSK_PUBLIC_DEMO_READONLY=1 msk-therapy-os-demo
curl -i http://127.0.0.1:7860/api/explore/search?q=stomach
curl -i http://127.0.0.1:7860/api/research/sets
curl -i -X POST http://127.0.0.1:7860/api/research/sets -H 'Content-Type: application/json' -d '{"title":"x"}'
# Last command must return 403 read-only.
```

`MSK_ATLAS_DATA_DIR` can point to a separate, legal Open Anatomy Atlas dataset mount following the expected `atlases/<version>/build/` layout. The source ZIP does **not** include complete BodyParts3D meshes. Treat any incomplete 3D scene as a blocking asset gap rather than a deployment success.

The Space runtime disk is ephemeral. A read-only seed database can be reinitialized safely. Future persistent SQLite clinical data require a separately validated storage/locking strategy and secure backend. Never upload patient photos or medical records to this public demo.

Official references: [Docker Space instructions](https://huggingface.co/docs/hub/spaces-sdks-docker), [Space storage behavior](https://huggingface.co/docs/hub/main/spaces-storage).

## Token gate

Only after security review, local Docker build/browser acceptance, license validation and verification that no secrets or personal data are in the repository, authenticated Space creation and push need an appropriately scoped token. Use Hugging Face settings **Secrets** for server tokens; never put tokens in Git, logs, HTML or screenshots. A token alone is not authorization to deploy identifiable patient information.
