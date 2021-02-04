import datetime
from calendar import timegm

from pyspiffe.svid import INVALID_INPUT_ERROR

from pyspiffe.svid.exceptions import (
    TokenExpiredError,
    InvalidClaimError,
    InvalidAlgorithmError,
    InvalidTypeError,
)

AUDIENCE_NOT_MATCH_ERROR = 'audience does not match expected value'


class JwtSvidValidator(object):
    """Performs validations on a given token checking compliance to SPIFFE specification.
    See `SPIFFE JWT-SVID standard <https://github.com/spiffe/spiffe/blob/master/standards/JWT-SVID.md>`

    """

    _REQUIRED_CLAIMS = ['aud', 'exp', 'sub']
    _SUPPORTED_ALGORITHMS = [
        'RS256',
        'RS384',
        'RS512',
        'ES256',
        'ES384',
        'ES512',
        'PS256',
        'PS384',
        'PS512',
    ]
    _SUPPORTED_TYPES = ['JWT', 'JOSE']

    def __init__(self) -> None:
        pass

    def validate_header(self, header: {}) -> None:
        """Validates token header by verifing if header specifies supported algortihms and token type. Type is optional but in case it is present, it must be set to the supported values.

        Args:
            header: token header.

        Returns:
            None.

        Raises:
            ValueError: in case header is not specified.
            InvalidAlgorithmError: in case specified 'alg' is not supported as specified by the SPIFFE standard.
            InvalidTypeError: in case 'typ' is present in header but is not set to 'JWT' or 'JOSE'.
        """
        if not header:
            raise ValueError(INVALID_INPUT_ERROR.format('header cannot be empty'))

        if header['alg'] not in self._SUPPORTED_ALGORITHMS:
            raise InvalidAlgorithmError(header['alg'])
        try:
            if header['typ'] and header['typ'] not in self._SUPPORTED_TYPES:
                raise InvalidTypeError(header['typ'])
        except KeyError:
            pass

    def validate_claims(self, payload: {}, expected_audience: []) -> None:
        """Validates payload for required claims (aud, exp, sub).

        Args:
            payload: token playload.
            expected_audience: audience as a list of strings used to validate the 'aud' claim.

        Returns:
            None

        Raises:
            InvalidClaimError: in case a required claim is not present in payload or expected_audience is not a subset of audience_claim.
            TokenExpiredError: in case token is expired.
            ValueError: in case expected_audience is empty.
        """
        try:
            for claim in self._REQUIRED_CLAIMS:
                if not payload[claim]:
                    raise InvalidClaimError(claim)
            self._validate_exp(payload['exp'])
            self._validate_aud(payload['aud'], expected_audience)
        except KeyError as key_error:
            raise InvalidClaimError(key_error.args[0])

    def _validate_exp(self, expiration_date: str) -> None:
        """Verifies expiration.
        Note: If and when https://github.com/jpadilla/pyjwt/issues/599 is fixed, this can be simplified/removed.

        Args:
            expiration_date: date to check if it is expired.

        Raises:
            TokenExpiredError: in case it is expired.
        """
        expiration_date = int(expiration_date)
        utctime = timegm(datetime.datetime.utcnow().utctimetuple())
        if expiration_date < utctime:
            raise TokenExpiredError()

    def _validate_aud(self, audience_claim: [], expected_audience: []) -> None:
        """Verifies if expected_audience is present in audience_claim. The aud claim MUST be present.

        Args:
            audience_claim: list of token's audience claim to be validated.
            expected_audience: list of the claims expected to be present in the token's audience claim.

        Raises:
            InvalidClaimError: in expected_audience is not a subset of audience_claim.
            ValueError: in case expected_audience is empty.
        """
        if not expected_audience:
            raise ValueError(
                INVALID_INPUT_ERROR.format('expected_audience cannot be empty')
            )

        if not audience_claim or all(aud == '' for aud in audience_claim):
            raise InvalidClaimError('audience_claim cannot be empty')

        if not all(aud in audience_claim for aud in expected_audience):
            raise InvalidClaimError(AUDIENCE_NOT_MATCH_ERROR)
