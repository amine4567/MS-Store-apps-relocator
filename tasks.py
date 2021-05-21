from invoke import task


@task
def run(c):
    c.run("python src/ui.py")


@task
def build(c):
    c.run("pyinstaller build.spec")


@task
def update_reqs(c):
    c.run("pip-compile src/requirements.in")


@task
def update_dev_reqs(c):
    c.run("pip-compile requirements-dev.in")
