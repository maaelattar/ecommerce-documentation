# 03 - UserProfileService

The `UserProfileService` is dedicated to managing user profile information, which includes personal details, contact information, preferences, and associated addresses. It operates on the `UserProfile` and `Address` entities, keeping this concern separate from core account management (`UserService`) and authentication (`AuthService`).

## 1. Responsibilities

*   **Profile Management (CRUD)**:
    *   Creating a `UserProfile` for a new user (often triggered after user registration).
    *   Retrieving a user's profile.
    *   Updating various aspects of a user's profile (e.g., first name, last name, date of birth, phone number, profile picture URL, preferences).
    *   Deleting a user profile (usually linked to user account deletion).
*   **Address Management (CRUD)**:
    *   Adding new addresses (shipping, billing) for a user.
    *   Retrieving a user's addresses (all, or by type).
    *   Updating existing addresses.
    *   Deleting addresses.
    *   Setting a default shipping or billing address.
*   **User Preferences**:
    *   Managing user-specific preferences (e.g., communication preferences, theme settings, language).
    *   These might be stored directly in the `UserProfile` entity or a separate related entity if complex.
*   **Data Validation**:
    *   Ensuring that profile and address data conforms to expected formats and constraints (e.g., valid phone numbers, postal codes).

## 2. Key Methods (Conceptual NestJS Example)

```typescript
import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm'; // Assuming TypeORM
import { Repository } from 'typeorm';
import { UserProfile } from '../entities/user-profile.entity';
import { Address } from '../entities/address.entity';
import { User } from '../entities/user.entity'; // To link profile and addresses to a user
import { CreateUserProfileDto } from '../dto/create-user-profile.dto';
import { UpdateUserProfileDto } from '../dto/update-user-profile.dto';
import { CreateAddressDto } from '../dto/create-address.dto';
import { UpdateAddressDto } from '../dto/update-address.dto';
import { UserEventPublisher } from './user-event-publisher.service';

@Injectable()
export class UserProfileService {
  constructor(
    @InjectRepository(UserProfile)
    private readonly userProfileRepository: Repository<UserProfile>,
    @InjectRepository(Address)
    private readonly addressRepository: Repository<Address>,
    // private readonly userService: UserService, // Optional: if needing to validate user existence
    private readonly userEventPublisher: UserEventPublisher,
  ) {}

  async createProfileForUser(userId: string, createProfileDto: CreateUserProfileDto): Promise<UserProfile> {
    // Ensure a profile doesn't already exist for this user
    const existingProfile = await this.userProfileRepository.findOne({ where: { user: { id: userId } } });
    if (existingProfile) {
      throw new BadRequestException(`Profile already exists for user ID ${userId}`);
    }

    const user = { id: userId } as User; // Assume user entity exists and we just need the ID for relation
    const profile = this.userProfileRepository.create({
      ...createProfileDto,
      user: user,
    });
    const savedProfile = await this.userProfileRepository.save(profile);
    await this.userEventPublisher.publishUserProfileCreated(savedProfile);
    return savedProfile;
  }

  async getProfileByUserId(userId: string): Promise<UserProfile | null> {
    return this.userProfileRepository.findOne({ 
        where: { user: { id: userId } },
        relations: ['addresses'] // Optionally load addresses with the profile
    });
  }

  async updateProfileByUserId(userId: string, updateProfileDto: UpdateUserProfileDto): Promise<UserProfile> {
    const profile = await this.getProfileByUserId(userId);
    if (!profile) {
      throw new NotFoundException(`Profile not found for user ID ${userId}`);
    }

    Object.assign(profile, updateProfileDto);
    const updatedProfile = await this.userProfileRepository.save(profile);
    await this.userEventPublisher.publishUserProfileUpdated(updatedProfile);
    return updatedProfile;
  }

  // --- Address Management ---

  async addAddress(userId: string, createAddressDto: CreateAddressDto): Promise<Address> {
    const profile = await this.getProfileByUserId(userId);
    if (!profile) {
        // Or, depending on design, could allow addresses linked directly to User if no UserProfile entity exists
        // For this example, we assume UserProfile is mandatory for addresses.
      throw new NotFoundException(`Profile not found for user ID ${userId}, cannot add address.`);
    }

    const address = this.addressRepository.create({
      ...createAddressDto,
      profile: profile, // Link address to the profile
    });
    const savedAddress = await this.addressRepository.save(address);
    // Event for address added might be useful: this.userEventPublisher.publishAddressAdded(savedAddress);
    return savedAddress;
  }

  async getAddressesByUserId(userId: string): Promise<Address[]> {
    const profile = await this.getProfileByUserId(userId);
    if (!profile) {
      // Return empty array or throw error based on desired behavior
      return []; 
    }
    // Assuming addresses are eagerly or lazily loaded with profile, or fetch separately:
    return this.addressRepository.find({ where: { profile: { id: profile.id } } });
  }

  async getAddressById(addressId: string): Promise<Address | null> {
    return this.addressRepository.findOneBy({ id: addressId });
  }

  async updateAddress(addressId: string, userId: string, updateAddressDto: UpdateAddressDto): Promise<Address> {
    // Ensure the address belongs to the user making the request (important authorization check)
    const address = await this.addressRepository.findOne({ 
        where: { id: addressId, profile: { user: { id: userId } } },
        relations: ['profile', 'profile.user']
    });
    
    if (!address) {
      throw new NotFoundException(`Address with ID ${addressId} not found or does not belong to user ID ${userId}.`);
    }

    Object.assign(address, updateAddressDto);
    const updatedAddress = await this.addressRepository.save(address);
    // Event for address updated: this.userEventPublisher.publishAddressUpdated(updatedAddress);
    return updatedAddress;
  }

  async deleteAddress(addressId: string, userId: string): Promise<void> {
    const address = await this.addressRepository.findOne({ 
        where: { id: addressId, profile: { user: { id: userId } } }
    });

    if (!address) {
      throw new NotFoundException(`Address with ID ${addressId} not found or does not belong to user ID ${userId}.`);
    }
    await this.addressRepository.remove(address);
    // Event for address deleted: this.userEventPublisher.publishAddressDeleted({ addressId, userId });
  }

  async setDefaultAddress(userId: string, addressId: string, type: 'shipping' | 'billing'): Promise<UserProfile> {
    const profile = await this.getProfileByUserId(userId);
    if (!profile) {
      throw new NotFoundException(`Profile not found for user ID ${userId}`);
    }

    const address = await this.addressRepository.findOne({where: {id: addressId, profile: {id: profile.id }}});
    if(!address) {
        throw new NotFoundException(`Address ID ${addressId} not found for this user.`);
    }

    if (type === 'shipping') {
      profile.defaultShippingAddressId = addressId;
    } else if (type === 'billing') {
      profile.defaultBillingAddressId = addressId;
    }
    const updatedProfile = await this.userProfileRepository.save(profile);
    await this.userEventPublisher.publishUserProfileUpdated(updatedProfile); // Or a more specific event
    return updatedProfile;
  }
}
```

## 3. Interactions

*   **`UserService`**: May be called to validate the existence of a `User` before creating a `UserProfile` for them, though often the `userId` is assumed to be valid as it comes from an authenticated context (e.g., JWT).
*   **`User` Entity**: `UserProfile` and `Address` entities have a relationship with the `User` entity (often `UserProfile` has a one-to-one with `User`, and `Address` has a many-to-one with `UserProfile` or `User`).
*   **Database**: Directly interacts with the `UserProfile` and `Address` tables.
*   **`UserEventPublisher`**: Publishes events like `UserProfileCreated`, `UserProfileUpdated`, `AddressAdded`, `AddressUpdated`, `AddressDeleted`.
*   **Other Services (e.g., Order Service, Shipping Service)**: These services would consume user profile and address information by querying the `UserProfileService` (typically via its API endpoints) when they need customer details for order processing, shipping calculations, etc.

## 4. Data Management & Integrity

*   **Referential Integrity**: Database foreign key constraints should ensure that profiles and addresses are correctly linked to existing users.
*   **Data Validation**: DTOs with validation rules for all input (e.g., valid phone numbers, email formats for secondary emails, postal codes, country codes).
*   **Consistency**: If a user account is deleted, corresponding profile and address data should also be handled (deleted or anonymized) according to policy.

## 5. Security Considerations

*   **Authorization**: Users should only be able to manage their own profile and addresses. API endpoints exposing `UserProfileService` methods must enforce this, typically by checking that the `userId` from the JWT matches the `userId` parameter in the request or the owner of the resource being accessed.
*   **PII (Personally Identifiable Information)**: Profile and address data is sensitive PII. Ensure it is handled securely:
    *   Encrypted in transit (HTTPS).
    *   Consider encryption at rest for sensitive fields if required by compliance.
    *   Limit access to this data within the system (principle of least privilege).
    *   Regularly audit access logs if available.
*   **Input Sanitization**: Sanitize any free-text fields to prevent XSS if this data is ever rendered directly in UIs without proper escaping (though backend services should generally not be responsible for frontend XSS protection).

## 6. Future Enhancements

*   **Profile Picture Management**: Storing profile pictures (e.g., in a cloud storage service like S3) and linking the URL in the profile, rather than storing image blobs in the database.
*   **Custom Profile Fields**: Allowing users or administrators to define custom fields for profiles.
*   **Version History**: Keeping a history of changes to profile information or addresses for auditing or rollback.
*   **Integration with Geocoding Services**: For validating or standardizing addresses.

`UserProfileService` provides a focused way to manage detailed user information beyond basic account credentials, enabling personalization and supporting other business processes that require this data.
