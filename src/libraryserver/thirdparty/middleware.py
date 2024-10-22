# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modified from:
# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/f7199c22c98d6234297fa7a21948c08608019018/run/idp-sql/middleware.py
# Maintained only portions needed to do jwt authentication


from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import firebase_admin
from firebase_admin import auth
from flask import request, Response


a = TypeVar("a")


def jwt_authenticated(func: Callable[..., int]) -> Callable[..., int]:
    """Use the Firebase Admin SDK to parse Authorization header to verify the
    user ID token.

    The server extracts the Identity Platform uid for that user.
    """

    @wraps(func)
    def decorated_function(*args: a, **kwargs: a) -> a:
        header = request.headers.get("Authorization", None)
        if header:
            token = header.split(" ")[1]
            try:
                decoded_token = firebase_admin.auth.verify_id_token(token)
            except Exception as e:
                logger.exception(e)
                return Response(status=403, response=f"Error with authentication: {e}")
        else:
            return Response(status=401)

        request.uid = decoded_token["uid"]
        return func(*args, **kwargs)

    return decorated_function
