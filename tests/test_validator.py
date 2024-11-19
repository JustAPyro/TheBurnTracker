from app.validator import Validate 

def test_contains_basic_true():
    p = Validate({
        'one': '1'
    }).contains('one').finalize()

    assert(len(p) == 0)

def test_contains_basic_false():
    data = {
        'one': '1'
    }

    p = (Validate(data).contains('one').contains('two').finalize())
    assert(len(p) == 1) 
    assert(p == [{
                'message': f'The provided data does not include the required field "two"',
                'path': 'two'
            }])

def test_contains_unknown():
    data = {
        'one': '1',
        'two': '2'
    }

    p = (Validate(data).contains('one').finalize())

    assert(len(p) == 1)
    assert(p == [{'message': 'The provided data contains the unexpected data field "two"', 'path': 'two'}])


def test_contains_unknown_false():
    data = {
        'one': '1'
    }
    
    p = (Validate(data)
         .contains('two')
         .finalize())

    assert(len(p) == 2)
    assert(p == [
        {'message': f'The provided data does not include the required field "two"', 'path': 'two'},
        {'message': 'The provided data contains the unexpected data field "one"', 'path': 'one'}
    ])
    
def test_contains_optional_true():
    data = {
        'one': '1',
        'two': '2'
    }

    p = (Validate(data).contains('one').optional('two').finalize())

    assert(len(p) == 0)
    assert(p == [])

def test_contains_optional_false():
    data = {
        'one': '1',
    }

    p = (Validate(data).contains('one').optional('two').finalize())

    assert(len(p) == 0)
    assert(p == [])

def test_contains_password_non_string():
    data = {
        'password': '12345xX'
    }

    p = (Validate(data)
         .contains('password', oftype='password')
         .finalize())

    assert(p == [{
                'message': f'The password field "password" must have more than 8 characters',
                'path': 'password'
            }])

def test_contains_password_non_string_non_complex():
    data = {
        'password': '1234567'
    }

    p = (Validate(data)
         .contains('password', oftype='password')
         .finalize())

    assert(p == [{
                'message': f'The password field "password" must have more than 8 characters',
                'path': 'password'
            },{
                'message': f'The password field "password" must have a lowercase, a capital, and a number',
                'path': 'password'
            }])

def test_contains_password_non_complex():
    data = {
        'password': 'xxxXXXxxx'
    }

    p = (Validate(data)
         .contains('password', oftype='password')
         .finalize())

    assert(p == [{
                'message': f'The password field "password" must have a lowercase, a capital, and a number',
                'path': 'password'
            }])


