# Aiobrute

Aiobrute is a tool for asynchronously testing password login on several protocols. It use the asyncio librairie instead of threads for testing password concurrently and efficiently.

DISCLAIMER: This software is for educational purposes only. This software should not be used for illegal activity.

---

### The following modules are currently supported

```
* http  :  test login for http protocol
* ftp   :  test login for ftp protocol
* ssh   :  test login for ssh protocol
* mysql :  test login for mysql protocol
```

### Some modules support multiple protocol

| Module | Protocol   | Description                                |
|------|--------------|--------------------------------------------|
| http   | http-form  | Testing html form authentication           |
| http   | basic-auth | Testing http basic authentication          |
| http   | wp-xmlrpc  | Testing wordpress xml-rpc authentication   |

### Some wordlists are also included

| Name        | Size  | Description                                      |
|-------------|-------|--------------------------------------------------|
| rockyou     | 59187 | Shorter version of the popular rockyou wordlist  |
| hotmail     | 8929  | Some Passwords from an old hotmail leak          |
| myspace     | 37120 | Some Passwords from an old myspace leak          |
| adobe       | 90    | Some Passwords from an old adobe leak            |
| mostused    | 200   | Most commonly used passwords                     |

## Installation & Usage

* #### Run aiobrute with docker

```
docker run -it --name aiobrute --rm blackice22/aiobrute <MODULE> <OPTIONS>
```

* #### Install aiobrute with pip

```
pip install aiobrute
```

---

## Output Examples

#### When no verbosity option are specified, a progress bar is displayed to the user with some statistics.

```
aiobrute http -t http://localhost:8080/wp-login.php -u admin -m POST -p http-form -c 302 -f USER:log PASS:pwd

    ░█████╗░██╗░█████╗░██████╗░██████╗░██╗░░░██╗████████╗███████╗
    ██╔══██╗██║██╔══██╗██╔══██╗██╔══██╗██║░░░██║╚══██╔══╝██╔════╝
    ███████║██║██║░░██║██████╦╝██████╔╝██║░░░██║░░░██║░░░█████╗░░
    ██╔══██║██║██║░░██║██╔══██╗██╔══██╗██║░░░██║░░░██║░░░██╔══╝░░
    ██║░░██║██║╚█████╔╝██████╦╝██║░░██║╚██████╔╝░░░██║░░░███████╗
    ╚═╝░░╚═╝╚═╝░╚════╝░╚═════╝░╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░╚══════╝

              https://github.com/jylanglois/aiobrute

                    version: [0.1.0 - alpha]

[-] Loading data from the 'rockyou' build in wordlist

Worker Type: http | Target: http://localhost:8080/wp-login.php | Workers: 15 | Wordlist Size: 59188

|█████████▏                              | ▅▃▁ 13455/59188 [23%] in 18s (730.3/s, eta: 1:03)
```

#### if verbosity options are specified, the status for each requests are printed in the console.

```
2022-04-15 11:16:20,925 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: 1234567 - (6 of 59188) - [worker 6]
2022-04-15 11:16:20,926 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: daniel - (10 of 59188) - [worker 10]
2022-04-15 11:16:20,927 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: 123456789 - (3 of 59188) - [worker 3]
2022-04-15 11:16:20,928 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: abc123 - (8 of 59188) - [worker 8]
2022-04-15 11:16:20,928 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: 12345 - (2 of 59188) - [worker 2]
2022-04-15 11:16:20,929 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: nicole - (9 of 59188) - [worker 9]
2022-04-15 11:16:20,929 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: 123456 - (1 of 59188) - [worker 1]
2022-04-15 11:16:20,930 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: iloveyou - (4 of 59188) - [worker 4]
2022-04-15 11:16:20,930 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: 12345678 - (7 of 59188) - [worker 7]
2022-04-15 11:16:20,931 - [HTTP] [INFO] - method: [POST] - status: [200] - target: http://localhost:8080/wp-login.php - username: admin - password: princess - (5 of 59188) - [worker 5]
```

---

## Usage Examples

### HTTP modules examples

* Test http html login form and validate the candidate if `302` status code is returned

```
aiobrute http -t http://localhost:8080/wp-login.php -u admin -m POST -p http-form -c 302 -f USER:log PASS:pwd
```

* Test http html login with a csrf token and validate the candidate if `302` status code is returned

```
aiobrute http -t http://localhost:8080/admin/login/ -u root -m POST -p http-form -c 302 -f USER:user PASS:pwd CSRF:csrftoken
```

* Test http login with basic authentication and validate the candidate if `401` status code is not returned

```
aiobrute http -t http://localhost:8080/ -u admin -m GET -p basic-auth -c ^401
```

* Test wordpress xml-rpc login and validate the candidate if the `faultCode` string is not found in the response

```
aiobrute http -t http://localhost:8080/xmlrpc.php -u admin -m POST -p wp-xmlrpc -s '^faultCode'
```

### Other modules examples

* Test ssh login with 5 concurrent worker and using the `mostused` built-in wordlist

```
aiobrute ssh -u admin -t localhost -w 5 -l mostused
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)