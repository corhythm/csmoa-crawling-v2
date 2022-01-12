from github import Github


def get_github_repo(access_token, repository_name):
    """
    github repo object를 얻는 함수
    :param access_token: Github access token
    :param repository_name: repo 이름
    :return: repo object
    """
    github = Github(access_token)
    repository = github.get_user().get_repo(repository_name)
    return repository


def upload_github_issue(repository, title, body):
    """
    해당 repository에 title 이름으로 issue를 생성하고, 내용을 body로 채우는 함수
    :param repository: repo 이름
    :param title: issue title
    :param body: issue body
    :return: None
    """
    repository.create_issue(title=title, body=body)
