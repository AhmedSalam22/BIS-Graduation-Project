from django.db import models
from django.conf import settings
# from phonenumber_field.modelfields import PhoneNumberField 
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ckeditor.fields import RichTextField

ISO_3166_CODES = [
    ('AF', _("Afghanistan")),
    ('AX', _("Aland Islands")),
    ('AL', _("Albania")),
    ('DZ', _("Algeria")),
    ('AS', _("American Samoa")),
    ('AD', _("Andorra")),
    ('AO', _("Angola")),
    ('AI', _("Anguilla")),
    ('AQ', _("Antarctica")),
    ('AG', _("Antigua And Barbuda")),
    ('AR', _("Argentina")),
    ('AM', _("Armenia")),
    ('AW', _("Aruba")),
    ('AU', _("Australia")),
    ('AT', _("Austria")),
    ('AZ', _("Azerbaijan")),
    ('BS', _("Bahamas")),
    ('BH', _("Bahrain")),
    ('BD', _("Bangladesh")),
    ('BB', _("Barbados")),
    ('BY', _("Belarus")),
    ('BE', _("Belgium")),
    ('BZ', _("Belize")),
    ('BJ', _("Benin")),
    ('BM', _("Bermuda")),
    ('BT', _("Bhutan")),
    ('BO', _("Bolivia, Plurinational State Of")),
    ('BQ', _("Bonaire, Saint Eustatius And Saba")),
    ('BA', _("Bosnia And Herzegovina")),
    ('BW', _("Botswana")),
    ('BV', _("Bouvet Island")),
    ('BR', _("Brazil")),
    ('IO', _("British Indian Ocean Territory")),
    ('BN', _("Brunei Darussalam")),
    ('BG', _("Bulgaria")),
    ('BF', _("Burkina Faso")),
    ('BI', _("Burundi")),
    ('KH', _("Cambodia")),
    ('CM', _("Cameroon")),
    ('CA', _("Canada")),
    ('CV', _("Cape Verde")),
    ('KY', _("Cayman Islands")),
    ('CF', _("Central African Republic")),
    ('TD', _("Chad")),
    ('CL', _("Chile")),
    ('CN', _("China")),
    ('CX', _("Christmas Island")),
    ('CC', _("Cocos (Keeling) Islands")),
    ('CO', _("Colombia")),
    ('KM', _("Comoros")),
    ('CG', _("Congo")),
    ('CD', _("Congo, The Democratic Republic Of The")),
    ('CK', _("Cook Islands")),
    ('CR', _("Costa Rica")),
    ('HR', _("Croatia")),
    ('CU', _("Cuba")),
    ('CW', _("Curacao")),
    ('CY', _("Cyprus")),
    ('CZ', _("Czech Republic")),
    ('DK', _("Denmark")),
    ('DJ', _("Djibouti")),
    ('DM', _("Dominica")),
    ('DO', _("Dominican Republic")),
    ('EC', _("Ecuador")),
    ('EG', _("Egypt")),
    ('SV', _("El Salvador")),
    ('GQ', _("Equatorial Guinea")),
    ('ER', _("Eritrea")),
    ('EE', _("Estonia")),
    ('ET', _("Ethiopia")),
    ('FK', _("Falkland Islands (Malvinas)")),
    ('FO', _("Faroe Islands")),
    ('FJ', _("Fiji")),
    ('FI', _("Finland")),
    ('FR', _("France")),
    ('GF', _("French Guiana")),
    ('PF', _("French Polynesia")),
    ('TF', _("French Southern Territories")),
    ('GA', _("Gabon")),
    ('GM', _("Gambia")),
    ('DE', _("Germany")),
    ('GH', _("Ghana")),
    ('GI', _("Gibraltar")),
    ('GR', _("Greece")),
    ('GL', _("Greenland")),
    ('GD', _("Grenada")),
    ('GP', _("Guadeloupe")),
    ('GU', _("Guam")),
    ('GT', _("Guatemala")),
    ('GG', _("Guernsey")),
    ('GN', _("Guinea")),
    ('GW', _("Guinea-Bissau")),
    ('GY', _("Guyana")),
    ('HT', _("Haiti")),
    ('HM', _("Heard Island and McDonald Islands")),
    ('VA', _("Holy See (Vatican City State)")),
    ('HN', _("Honduras")),
    ('HK', _("Hong Kong")),
    ('HU', _("Hungary")),
    ('IS', _("Iceland")),
    ('IN', _("India")),
    ('ID', _("Indonesia")),
    ('IR', _("Iran, Islamic Republic Of")),
    ('IQ', _("Iraq")),
    ('IE', _("Ireland")),
    ('IL', _("Israel")),
    ('IT', _("Italy")),
    ('CI', _("Ivory Coast")),
    ('JM', _("Jamaica")),
    ('JP', _("Japan")),
    ('JE', _("Jersey")),
    ('JO', _("Jordan")),
    ('KZ', _("Kazakhstan")),
    ('KE', _("Kenya")),
    ('KI', _("Kiribati")),
    ('KP', _("Korea, Democratic People's Republic Of")),
    ('KR', _("Korea, Republic Of")),
    ('KS', _("Kosovo")),
    ('KW', _("Kuwait")),
    ('KG', _("Kyrgyzstan")),
    ('LA', _("Lao People's Democratic Republic")),
    ('LV', _("Latvia")),
    ('LB', _("Lebanon")),
    ('LS', _("Lesotho")),
    ('LR', _("Liberia")),
    ('LY', _("Libyan Arab Jamahiriya")),
    ('LI', _("Liechtenstein")),
    ('LT', _("Lithuania")),
    ('LU', _("Luxembourg")),
    ('MO', _("Macao")),
    ('MK', _("Macedonia")),
    ('MG', _("Madagascar")),
    ('MW', _("Malawi")),
    ('MY', _("Malaysia")),
    ('MV', _("Maldives")),
    ('ML', _("Mali")),
    ('ML', _("Malta")),
    ('MH', _("Marshall Islands")),
    ('MQ', _("Martinique")),
    ('MR', _("Mauritania")),
    ('MU', _("Mauritius")),
    ('YT', _("Mayotte")),
    ('MX', _("Mexico")),
    ('FM', _("Micronesia")),
    ('MD', _("Moldova")),
    ('MC', _("Monaco")),
    ('MN', _("Mongolia")),
    ('ME', _("Montenegro")),
    ('MS', _("Montserrat")),
    ('MA', _("Morocco")),
    ('MZ', _("Mozambique")),
    ('MM', _("Myanmar")),
    ('NA', _("Namibia")),
    ('NR', _("Nauru")),
    ('NP', _("Nepal")),
    ('NL', _("Netherlands")),
    ('AN', _("Netherlands Antilles")),
    ('NC', _("New Caledonia")),
    ('NZ', _("New Zealand")),
    ('NI', _("Nicaragua")),
    ('NE', _("Niger")),
    ('NG', _("Nigeria")),
    ('NU', _("Niue")),
    ('NF', _("Norfolk Island")),
    ('MP', _("Northern Mariana Islands")),
    ('NO', _("Norway")),
    ('OM', _("Oman")),
    ('PK', _("Pakistan")),
    ('PW', _("Palau")),
    ('PS', _("Palestinian Territory, Occupied")),
    ('PA', _("Panama")),
    ('PG', _("Papua New Guinea")),
    ('PY', _("Paraguay")),
    ('PE', _("Peru")),
    ('PH', _("Philippines")),
    ('PN', _("Pitcairn")),
    ('PL', _("Poland")),
    ('PT', _("Portugal")),
    ('PR', _("Puerto Rico")),
    ('QA', _("Qatar")),
    ('RE', _("Reunion")),
    ('RO', _("Romania")),
    ('RU', _("Russian Federation")),
    ('RW', _("Rwanda")),
    ('BL', _("Saint Barthelemy")),
    ('SH', _("Saint Helena, Ascension & Tristan Da Cunha")),
    ('KN', _("Saint Kitts and Nevis")),
    ('LC', _("Saint Lucia")),
    ('MF', _("Saint Martin (French Part)")),
    ('PM', _("Saint Pierre and Miquelon")),
    ('VC', _("Saint Vincent And The Grenadines")),
    ('WS', _("Samoa")),
    ('SM', _("San Marino")),
    ('ST', _("Sao Tome And Principe")),
    ('SA', _("Saudi Arabia")),
    ('SN', _("Senegal")),
    ('RS', _("Serbia")),
    ('SC', _("Seychelles")),
    ('SL', _("Sierra Leone")),
    ('SG', _("Singapore")),
    ('SX', _("Sint Maarten (Dutch Part)")),
    ('SK', _("Slovakia")),
    ('SI', _("Slovenia")),
    ('SB', _("Solomon Islands")),
    ('SO', _("Somalia")),
    ('ZA', _("South Africa")),
    ('GS', _("South Georgia And The South Sandwich Islands")),
    ('ES', _("Spain")),
    ('LK', _("Sri Lanka")),
    ('SD', _("Sudan")),
    ('SR', _("Suriname")),
    ('SJ', _("Svalbard And Jan Mayen")),
    ('SZ', _("Swaziland")),
    ('SE', _("Sweden")),
    ('CH', _("Switzerland")),
    ('SY', _("Syrian Arab Republic")),
    ('TW', _("Taiwan")),
    ('TJ', _("Tajikistan")),
    ('TZ', _("Tanzania")),
    ('TH', _("Thailand")),
    ('TL', _("Timor-Leste")),
    ('TG', _("Togo")),
    ('TK', _("Tokelau")),
    ('TO', _("Tonga")),
    ('TT', _("Trinidad and Tobago")),
    ('TN', _("Tunisia")),
    ('TR', _("Turkey")),
    ('TM', _("Turkmenistan")),
    ('TC', _("Turks And Caicos Islands")),
    ('TV', _("Tuvalu")),
    ('UG', _("Uganda")),
    ('UA', _("Ukraine")),
    ('AE', _("United Arab Emirates")),
    ('GB', _("United Kingdom")),
    ('US', _("United States")),
    ('UM', _("United States Minor Outlying Islands")),
    ('UY', _("Uruguay")),
    ('UZ', _("Uzbekistan")),
    ('VU', _("Vanuatu")),
    ('VE', _("Venezuela, Bolivarian Republic Of")),
    ('VN', _("Viet Nam")),
    ('VG', _("Virgin Islands, British")),
    ('VI', _("Virgin Islands, U.S.")),
    ('WF', _("Wallis and Futuna")),
    ('EH', _("Western Sahara")),
    ('YE', _("Yemen")),
    ('ZM', _("Zambia")),
    ('ZW', _("Zimbabwe")),
]
# Create your models here.
class CustomerType(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_type = models.CharField(max_length=250 , blank=False)

    def __str__(self):
        return self.customer_type

class Customer(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name  = models.CharField(max_length=50)
    last_name   = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50 , blank=True , null=True)
    account_number = models.IntegerField(blank=True , null=True)
    prospect = models.BooleanField()
    inactive = models.BooleanField()
    customer_type = models.ForeignKey(CustomerType , on_delete=models.CASCADE , blank=True , null=True)

    @property
    def full_name(self):
        """Returns the customer's full name."""
        return f'{self.first_name} {self.middle_name if self.middle_name != None else ""} {self.last_name}'

    def __str__(self):
        return self.full_name

class CustomerCommonFields(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    class Meta:
        abstract = True



class CustomerEmail(CustomerCommonFields):
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.email

# class Telephone (CustomerCommonFields):
#     phone_number = PhoneNumberField(blank=True , region="EG")

#     def __str__(self):
#         return f"{self.phone_number}"



def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'customer_sales/cutomer_imgs/user_{0}/{2}{1}'.format(instance.owner.id, filename , timezone.now())

class CustomerImage(CustomerCommonFields):
    image = models.ImageField(upload_to=user_directory_path,
                                null=True,
                                blank=True,
                                editable=True,
                                help_text="Customer Picture",
                             )
    
    def __str__(self):
        return f"img:{self.customer.first_name} {self.customer.middle_name} {self.customer.last_name}"

    
class CustomerAddress(CustomerCommonFields):
    address1 = models.CharField(
        "Address line 1",
        max_length=1024,
        blank=True ,
        null=True
    )


    address2 = models.CharField(
        "Address line 2",
        max_length=1024,
        null = True,
        blank= True
    )

    zip_code = models.CharField(
        "ZIP / Postal code",
        max_length=12,
        blank=True ,
        null=True
    )

    city = models.CharField(
        "City",
        max_length=1024,
        blank=True ,
        null=True
    )

    country = models.CharField(
        "Country",
        max_length=3,
        choices=ISO_3166_CODES,
        blank=True ,
        null=True
    )

    def __str__(self):
        return f"{self.customer.first_name} {self.customer.middle_name} {self.customer.last_name}:{self.address1}"

        

class CustomerNote(CustomerCommonFields):
    note = RichTextField(blank=True , null=True)

    def __str__(self):
        return f"note:{self.customer.first_name} {self.customer.middle_name} {self.customer.last_name}"



