/**
 * Copyright 2021 Google LLC
 * Licensed under the Apache License, Version 2.0 (the `License`);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an `AS IS` BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * 
 * Modified to be a simplified example of auth with the Library app.
 */

const config = {
  apiKey: "AIzaSyAMfrocCYIR9411DpaEYbvHI3mEweM1JwE",
  authDomain: "run-web.firebaseapp.com",
};
firebase.initializeApp(config);

// Watch for state change from sign in
function initApp() {
  firebase.auth().onAuthStateChanged(user => {
    if (user) {
      // User is signed in.
      document.getElementById('signInButton').innerText = 'Sign Out';
      return validateUser().then(valid => {
        if (valid) {
          document.getElementById('actions').style.display = '';
        } else {
          document.getElementById('actions').style.display = 'none';
          window.alert(`Sign in successful, but user is not authorized.`);
        }
      });
    } else {
      // No user is signed in.
      document.getElementById('signInButton').innerText = 'Sign in';
      document.getElementById('actions').style.display = 'none';
    }
  });
}
window.onload = function () {
  initApp();
};

function signIn() {
  const provider = new firebase.auth.GoogleAuthProvider();
  provider.addScope('https://www.googleapis.com/auth/userinfo.email');
  firebase
    .auth()
    .signInWithPopup(provider)
    .then(result => {
      // Returns the signed in user along with the provider's credential
      console.log(`${result.user.displayName} logged in.`);
    })
    .catch(err => {
      console.log(`Error during sign in: ${err.message}`);
      window.alert(`Sign in failed. Retry or check your browser logs.`);
    });
}

function signOut() {
  firebase
    .auth()
    .signOut()
    .then(result => {})
    .catch(err => {
      console.log(`Error during sign out: ${err.message}`);
      window.alert(`Sign out failed. Retry or check your browser logs.`);
    });
}

// Toggle Sign in/out button
function toggle() {
  if (!firebase.auth().currentUser) {
    signIn();
  } else {
    signOut();
  }
}

async function validateUser() {
  if (firebase.auth().currentUser) {
    try {
      const token = await firebase.auth().currentUser.getIdToken();
      const response = await fetch('/v0/check', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        return true;
      }
    } catch (err) {
      console.log(`Error when validating user: ${err}`);
    }
  }
  return false;
}

async function requestWrapper(doRequest) {
  if (firebase.auth().currentUser) {
    // Retrieve JWT to identify the user to the Identity Platform service.
    // Returns the current token if it has not expired. Otherwise, this will
    // refresh the token and return a new one.
    try {
      const token = await firebase.auth().currentUser.getIdToken();
      const response = await doRequest(token)
      if (response.ok) {
        const text = await response.text();
        window.alert(text);
        window.location.reload();
      }
    } catch (err) {
      console.log(`Error when submitting vote: ${err}`);
      window.alert('Something went wrong... Please try again!');
    }
  } else {
    window.alert('User not signed in.');
  }
}

async function getBook() {
  const isbn = document.getElementById("isbn").value;
  requestWrapper(token => {
    return fetch(`/v0/books/${isbn}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  })
}

async function listBooks() {
  requestWrapper(token => {
    return fetch('/v0/books', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  })
}

async function listUsers() {
  requestWrapper(token => {
    return fetch('/v0/users', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  })
}