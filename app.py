import flask
from mako.template import Template
from mako.lookup import TemplateLookup

mako_lookup = TemplateLookup(directories=['templates'])


def render(tpl, **kwargs):
    return mako_lookup.get_template(tpl).render(**kwargs)


app = flask.Flask(__name__)


@app.route('/')
@app.route('/register')
def register():

    return render('register.mako', title="done")


if __name__ == '__main__':
    app.run(debug=True)