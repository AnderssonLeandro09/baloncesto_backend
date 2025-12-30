from .persona import PersonaSerializer  # noqa: F401
from .administrador import (  # noqa: F401
    AdministradorSerializer,
    AdministradorDataSerializer,
    AdministradorInputSerializer,
    AdministradorResponseSerializer,
)
from .estudiante_vinculacion import (  # noqa: F401
    EstudianteVinculacionSerializer,
    EstudianteVinculacionDataSerializer,
    EstudianteVinculacionInputSerializer,
    EstudianteVinculacionResponseSerializer,
)
from .entrenador import (  # noqa: F401
    EntrenadorSerializer,
    EntrenadorDataSerializer,
    EntrenadorInputSerializer,
    EntrenadorResponseSerializer,
)
from .auth import LoginSerializer  # noqa: F401
from .inscripcion import InscripcionSerializer  # noqa: F401
from .atleta import (  # noqa: F401
    AtletaSerializer,
    AtletaDataSerializer,
    InscripcionDataSerializer,
    AtletaInscripcionInputSerializer,
    AtletaInscripcionResponseSerializer,
)
from .prueba_fisica import (  # noqa: F401
    PruebaFisicaSerializer,
    PruebaFisicaInputSerializer,
    PruebaFisicaResponseSerializer,
)
from .profile import (  # noqa: F401
    ProfileResponseSerializer,
)
