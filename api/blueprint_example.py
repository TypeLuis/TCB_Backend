from flask import Blueprint

example_blueprint = Blueprint("blueprint_example", __name__) #inside of "blueprint_example" string should be the name of the file

@example_blueprint.route('/example', methods=['GET'])
def example():
    return {"message": 'This is a blueprint example'}