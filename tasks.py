from invoke import task


@task
def run(c):
    c.run("python src/ui.py")


@task
def build(c):
    c.run("pyinstaller build.spec")
