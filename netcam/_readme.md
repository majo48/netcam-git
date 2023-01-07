#Apache setup

Serve the pages using Apache via WSGI which helps to get our code deployed on Apache.

#Apache config file
/etc/apache2/sites-available/mynetcams.com.conf

    <VirtualHost *:80>
        ServerAdmin webmaster@mynetcams.com
        ServerName www.mynetcams.com
        ServerAlias mynetcams.com
        ErrorLog /var/log/netcam-error.log
        CustomLog /var/log/netcam-access.log combined

        WSGIDaemonProcess netcam-app user=www-data group=www-data threads=5
        WSGIProcessGroup netcam-app
        WSGIScriptAlias / /var/www/html/netcam-git/netcam/netcam-app.wsgi
        Alias /static/ /var/www/html/netcam-git/netcam/static
        <Directory /var/www/html/netcam-git/netcam/static>
            Order allow,deny
            Allow from all
        </Directory>

    </VirtualHost>