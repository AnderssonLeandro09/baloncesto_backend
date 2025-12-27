# Tests del módulo Basketball
# Importar todos los tests de los submódulos para que Django los descubra

from basketball.tests.dao import *  # noqa: F401,F403
from basketball.tests.services import *  # noqa: F401,F403
from basketball.tests.controllers import *  # noqa: F401,F403
