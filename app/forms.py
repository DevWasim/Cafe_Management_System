from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, SelectField, DateField, TimeField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User, Supplier
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    price = FloatField('Selling Price ($)', validators=[DataRequired()])
    cost = FloatField('Cost Price ($) (For Profit Calc)', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('Coffee', 'Coffee'), 
        ('Tea', 'Tea'), 
        ('Snacks', 'Snacks'), 
        ('Desserts', 'Desserts'),
        ('Beverages', 'Beverages'),
        ('Main Course', 'Main Course')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image_file = FileField('Item Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    
    # Custom Options (Comma separated)
    sizes = StringField('Sizes (e.g., Small, Medium, Large)', validators=[Optional()])
    sugar_levels = StringField('Sugar Levels (e.g., 0%, 50%, 100%)', validators=[Optional()])
    add_ons = StringField('Add-ons (e.g., Extra shot, Whipped cream)', validators=[Optional()])
    
    is_available = BooleanField('Available (In Stock)')
    is_featured = BooleanField('Featured on Home Page')
    submit = SubmitField('Save Item')

class TableForm(FlaskForm):
    table_number = IntegerField('Table Number', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Available', 'Available'), ('Occupied', 'Occupied'), ('Reserved', 'Reserved')])
    submit = SubmitField('Save Table')

# -- Staff Management Forms --

class StaffForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    role = SelectField('Role', choices=[('Manager', 'Manager'), ('Chef', 'Chef'), ('Waiter', 'Waiter'), ('Cashier', 'Cashier')], validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    hourly_rate = FloatField('Hourly Rate ($)', validators=[Optional()])
    submit = SubmitField('Save Staff')

class ShiftForm(FlaskForm):
    user_id = SelectField('Staff Member', coerce=int, validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Start Time', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])
    notes = StringField('Notes', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Assign Shift')

class AttendanceForm(FlaskForm):
    user_id = SelectField('Staff Member', coerce=int, validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    clock_in = DateTimeField('Clock In', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    clock_out = DateTimeField('Clock Out', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    status = SelectField('Status', choices=[('Present', 'Present'), ('Late', 'Late'), ('Absent', 'Absent'), ('On Leave', 'On Leave')])
    submit = SubmitField('Save Record')

class InventoryItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = StringField('Unit (e.g., kg, L, pcs)', validators=[DataRequired()])
    low_stock_threshold = FloatField('Low Stock Threshold', validators=[Optional()], default=5.0)
    cost_per_unit = FloatField('Cost per Unit ($)', validators=[Optional()], default=0.0)
    submit = SubmitField('Save Ingredient')

class SupplierForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    contact_name = StringField('Contact Person', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Supplier')

class PurchaseForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    reference = StringField('Reference / Invoice #', validators=[Optional()])
    # Items will be handled separately or added here if we use FieldList (complex)
    # For now, let's keep it simple: Create Purchase Header -> Add Items
    submit = SubmitField('Create Purchase Record')

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(min=3, max=20)])
    discount_value = FloatField('Discount Value', validators=[DataRequired()])
    discount_type = SelectField('Discount Type', choices=[('Percentage', 'Percentage (%)'), ('Fixed Amount', 'Fixed Amount ($)')], validators=[DataRequired()])
    valid_from = DateTimeField('Valid From', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], default=datetime.now)
    valid_to = DateTimeField('Valid To', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    usage_limit = IntegerField('Usage Limit', validators=[Optional()], default=100)
    active = BooleanField('Active')
    submit = SubmitField('Save Coupon')

class SettingsForm(FlaskForm):
    # General
    cafe_name = StringField('Cafe Name', validators=[DataRequired()])
    cafe_logo = FileField('Cafe Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    cafe_address = TextAreaField('Address')
    cafe_phone = StringField('Phone')
    cafe_email = StringField('Email', validators=[Optional(), Email()])
    
    # Financials
    tax_rate = FloatField('Tax Rate (%)', validators=[Optional()])
    service_charge = FloatField('Service Charge (%)', validators=[Optional()])
    currency_symbol = StringField('Currency Symbol', validators=[DataRequired(), Length(max=5)])
    
    # Operations
    opening_time = TimeField('Opening Time', format='%H:%M', validators=[Optional()])
    closing_time = TimeField('Closing Time', format='%H:%M', validators=[Optional()])
    
    # Tech
    printer_ip = StringField('Printer IP')
    printer_port = IntegerField('Printer Port', validators=[Optional()])
    pos_enabled = BooleanField('Enable POS Integration')
    language = SelectField('Language', choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French')], default='en')
    
    # Home Page
    hero_title = StringField('Hero Title')
    hero_subtitle = StringField('Hero Subtitle')
    hero_image = FileField('Hero Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    short_description = TextAreaField('Short Description')

    submit = SubmitField('Save Settings')

class FrontendSettingsForm(FlaskForm):
    # Style
    # Story & Values
    story_title = StringField('Story Title')
    story_content = TextAreaField('Story Content')
    story_image = FileField('Story Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    mission_content = TextAreaField('Mission Statement')
    vision_content = TextAreaField('Vision Statement')

    # Styles
    theme_color_primary = StringField('Primary Color', validators=[DataRequired()])
    theme_color_secondary = StringField('Secondary Color', validators=[DataRequired()])
    menu_bg_color = StringField('Menu Background Color', validators=[DataRequired()])
    card_bg_color = StringField('Card Background Color', validators=[DataRequired()])
    text_color = StringField('Text Color', validators=[DataRequired()])
    
    # Hero (Consolidated here)
    hero_title = StringField('Hero Title')
    hero_subtitle = StringField('Hero Subtitle')
    hero_image = FileField('Hero Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    short_description = TextAreaField('Short Description')
    
    # About Us
    about_title = StringField('About Title')
    about_content = TextAreaField('About Content')
    about_image = FileField('About Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    
    # Socials
    social_facebook = StringField('Facebook URL')
    social_instagram = StringField('Instagram URL')
    social_twitter = StringField('Twitter/X URL')
    
    submit = SubmitField('Update Frontend')

class TeamMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[Optional()])
    image_file = FileField('Profile Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    is_visible = BooleanField('Visible on Site', default=True)
    submit = SubmitField('Save Team Member')

class CafePhotoForm(FlaskForm):
    image_file = FileField('Photo', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'])])
    caption = StringField('Caption', validators=[Optional()])
    is_visible = BooleanField('Visible', default=True)
    submit = SubmitField('Upload Photo')
