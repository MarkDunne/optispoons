# Optispoons

## Todo

- [ ] Restructure the code into an app directory
- [ ] Deploy


## Run book

**To run the service**

```bash
poetry run uvicorn main:app --reload --port 8000
```

**To run the tests**
```bash
poetry run python -m pytest tests
```
There is also a 

**To track and untrack `.env`**

```bash
git update-index --assume-unchanged [<file> ...]
git update-index --no-assume-unchanged [<file> ...]
```