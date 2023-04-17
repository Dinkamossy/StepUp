from step_up.__init__ import create_app

if __name__ == '__main__':
    application = create_app()
    application.app_context().push()
    application.run(host='127.0.0.1')