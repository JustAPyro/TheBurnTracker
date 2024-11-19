from typing import Self
import re
class Validate:
    def __init__(self, d: dict):
        self.d = d
        self.found = []
        self.problems = []
        

    def contains(self, field: str, oftype: str = None) -> Self:
        if field not in self.d.keys():
            self.problems.append({
                'message': f'The provided data does not include the required field "{field}"',
                'path': field
            })
        elif oftype != None:
            try:
                method = getattr(Validate, f'_type_{oftype}')
                method(self, field=field)
            except:
                pass


        self.found.append(field)
        return self

    def optional(self, field: str) -> Self:
        self.found.append(field)
        return self

    def finalize(self) -> list:

        for field in self.d.keys():
            if field not in self.found:
                self.problems.append({
                    'message': f'The provided data contains the unexpected data field "{field}"',
                    'path': field
                })

        return self.problems

    def _type_password(self, field):
        pwd = str(self.d.get(field))

        # Passwords are required to have > 8 characters
        if len(pwd) < 8:
            self.problems.append({
                'message': f'The password field "{field}" must have more than 8 characters',
                'path': field
            })

        # Passwords are required to have an uppercase, lowercase and a number
        if not (
            re.search(r'[A-Z]', pwd) and
            re.search(r'[a-z]', pwd) and
            re.search(r'[1-9]', pwd)
        ):
            self.problems.append({
                'message': f'The password field "{field}" must have a lowercase, a capital, and a number',
                'path': field
            })




