.. _updates_fork:

Updates and Development using Fork
==================================

Updating required packages
--------------------------

If you need to upgrade required packages for OpenNFT, use following command in terminal

.. code-block::

    pip install -r requirements.txt --upgrade

If you need to downgrade a specific package due to its unstable work

.. code-block::

    pip install <PACKAGE_NAME>==<VERSION>

Updating your Fork from OpenNFT repository
------------------------------------------

If you have your own repository forked from original OpenNFT, you can update it in the following way

.. image:: _static/updates_1.png

Press ''Fetch upstream'' to update your repository. If you are too behind in commits history, you will have to open pull request and resolve all conflicts

.. image:: _static/updates_2.png

Otherwise, if there is no conflicts, you can press ''Fetch and merge'' to update your fork

.. image:: _static/updates_3.png

Resolving conflicts via PyCharm
-------------------------------

In case if you faced conflicts which you can not resolve using GitHub, you can do following steps to resolve them manually

1. Go to Git -> Manage remotes and add OpenNFT original repository as remote branch
2. Use Git menu in the bottom right part of your screen to checkout to master branch of original OpenNFT
3. Return to your master branch and using the same Git menu press "Merge into current" on original master branch

After that you wil be able to resolve all conflicts manually.

Checking pull requests locally
------------------------------

Following command in terminal will help if you want to check pull request to your fork locally

.. code-block::

    git fetch origin pull/<ID>/head:<BRANCHNAME>
    git checkout <BRANCHNAME>

