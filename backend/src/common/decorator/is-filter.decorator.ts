import {
  ValidationOptions,
  registerDecorator,
  ValidationArguments,
} from 'class-validator';

export const IsFilter = (validationOptions?: ValidationOptions) => {
  return (object: any, propertyName: string) => {
    registerDecorator({
      name: 'isFilter',
      target: object.constructor,
      propertyName: propertyName,
      constraints: [],
      options: validationOptions,
      validator: {
        validate(value: any) {
          if (!Array.isArray(value)) {
            return false;
          }
          return value.every((v) => v >= 1 && v <= 6);
        },
        defaultMessage(args: ValidationArguments) {
          return 'Default message for ' + propertyName;
        },
      },
    });
  };
};
