from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models import (
    User, Salon, Service, Stylist, Appointment,
    AppointmentStatus, AppointmentType, UserRole
)
from app.schemas import (
    Appointment as AppointmentSchema,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentDetail,
    AppointmentStatusUpdate,
    AppointmentPaymentUpdate,
    TimeSlot,
    AvailabilityRequest
)
from app.auth import (
    get_current_active_user,
    get_client,
    get_salon_staff,
    get_any_user
)

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)

@router.post("", response_model=AppointmentDetail, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_client)
):
    """
    Create a new appointment (clients only)
    
    Args:
        appointment_data: Appointment creation data
        db: Database session
        current_user: Current authenticated client
        
    Returns:
        Created appointment data
        
    Raises:
        HTTPException: If service, stylist not found, or there's a time conflict
    """
    # Get the service
    service = db.query(Service).filter(
        Service.id == appointment_data.service_id,
        Service.is_active == True
    ).first()
    
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive"
        )
    
    # Get the stylist
    stylist = db.query(Stylist).filter(
        Stylist.id == appointment_data.stylist_id,
        Stylist.is_active == True
    ).first()
    
    if stylist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found or inactive"
        )
    
    # Verify that stylist offers this service
    if service not in stylist.services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stylist does not offer this service"
        )
    
    # Calculate end time
    end_time = appointment_data.start_time + timedelta(minutes=service.duration_minutes)
    
    # Check for time conflicts with other appointments
    conflicting_appointment = db.query(Appointment).filter(
        Appointment.stylist_id == stylist.id,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
        or_(
            and_(
                Appointment.start_time <= appointment_data.start_time,
                Appointment.end_time > appointment_data.start_time
            ),
            and_(
                Appointment.start_time < end_time,
                Appointment.end_time >= end_time
            ),
            and_(
                Appointment.start_time >= appointment_data.start_time,
                Appointment.end_time <= end_time
            )
        )
    ).first()
    
    if conflicting_appointment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot is not available"
        )
    
    # Check stylist working hours
    # This is a simplified check - in a real app, we'd check the stylist's working hours more thoroughly
    if stylist.working_hours:
        day_of_week = appointment_data.start_time.strftime("%A").lower()
        if day_of_week in stylist.working_hours:
            # Check if appointment time is within working hours
            is_within_hours = False
            for time_slot in stylist.working_hours.get(day_of_week, []):
                start_hour, start_minute = map(int, time_slot["start"].split(":"))
                end_hour, end_minute = map(int, time_slot["end"].split(":"))
                
                work_start = appointment_data.start_time.replace(
                    hour=start_hour, minute=start_minute, second=0, microsecond=0
                )
                work_end = appointment_data.start_time.replace(
                    hour=end_hour, minute=end_minute, second=0, microsecond=0
                )
                
                if appointment_data.start_time >= work_start and end_time <= work_end:
                    is_within_hours = True
                    break
            
            if not is_within_hours:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Appointment time is outside of stylist's working hours"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stylist does not work on {day_of_week}"
            )
    
    # Calculate price
    price = service.price
    additional_fees = 0
    
    # Add fee for at-home services
    if appointment_data.appointment_type == AppointmentType.AT_HOME and service.home_service_fee:
        additional_fees = service.home_service_fee
    
    # Create appointment
    new_appointment = Appointment(
        client_id=current_user.id,
        service_id=service.id,
        stylist_id=stylist.id,
        start_time=appointment_data.start_time,
        end_time=end_time,
        appointment_type=appointment_data.appointment_type,
        address=appointment_data.address,
        notes=appointment_data.notes,
        status=AppointmentStatus.PENDING,
        price=price + additional_fees,
        original_price=price,
        additional_fees=additional_fees,
        discount_amount=0,
        is_paid=False
    )
    
    # Save to database
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    
    return new_appointment

@router.get("/my-appointments", response_model=List[AppointmentDetail])
async def get_my_appointments(
    status: Optional[AppointmentStatus] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's appointments
    
    Args:
        status: Filter by appointment status
        from_date: Filter by start date (inclusive)
        to_date: Filter by end date (inclusive)
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of appointments
    """
    # Base query
    if current_user.role == UserRole.CLIENT:
        # Client sees their bookings
        query = db.query(Appointment).filter(Appointment.client_id == current_user.id)
    elif current_user.role == UserRole.STYLIST:
        # Stylist sees appointments assigned to them
        query = db.query(Appointment).filter(Appointment.stylist_id == current_user.id)
    elif current_user.role == UserRole.SALON_OWNER:
        # Salon owner sees all appointments in their salons
        salon_ids = [salon.id for salon in db.query(Salon).filter(Salon.owner_id == current_user.id).all()]
        stylist_ids = [stylist.id for stylist in db.query(Stylist).filter(Stylist.salon_id.in_(salon_ids)).all()]
        query = db.query(Appointment).filter(Appointment.stylist_id.in_(stylist_ids))
    else:
        # Admin sees all appointments
        query = db.query(Appointment)
    
    # Apply filters
    if status:
        query = query.filter(Appointment.status == status)
    
    if from_date:
        query = query.filter(Appointment.start_time >= from_date)
    
    if to_date:
        query = query.filter(Appointment.start_time <= to_date)
    
    # Order by start time and apply pagination
    appointments = query.order_by(Appointment.start_time.desc()).offset(skip).limit(limit).all()
    
    return appointments

@router.get("/availability", response_model=List[TimeSlot])
async def check_availability(
    service_id: int,
    date: datetime,
    stylist_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Check available time slots for a service
    
    Args:
        service_id: Service ID
        date: Date to check
        stylist_id: Optional stylist ID
        db: Database session
        
    Returns:
        List of available time slots
    """
    # Get the service
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.is_active == True
    ).first()
    
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive"
        )
    
    # Get stylists who offer this service
    query = db.query(Stylist).filter(
        Stylist.is_active == True,
        Stylist.services.any(Service.id == service_id)
    )
    
    if stylist_id:
        query = query.filter(Stylist.id == stylist_id)
    
    stylists = query.all()
    
    if not stylists:
        return []
    
    # Initialize result list
    available_slots = []
    
    # Get day of week for date
    day_of_week = date.strftime("%A").lower()
    
    # Check each stylist's availability
    for stylist in stylists:
        # Skip if stylist doesn't work on this day
        if not stylist.working_hours or day_of_week not in stylist.working_hours:
            continue
        
        # Get stylist's working hours for this day
        working_hours = stylist.working_hours.get(day_of_week, [])
        
        for time_slot in working_hours:
            # Parse working hours
            start_hour, start_minute = map(int, time_slot["start"].split(":"))
            end_hour, end_minute = map(int, time_slot["end"].split(":"))
            
            # Create datetime objects for start and end of working hours
            work_start = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            work_end = date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            # Generate potential time slots (every 30 minutes)
            slot_start = work_start
            service_duration = timedelta(minutes=service.duration_minutes)
            
            while slot_start + service_duration <= work_end:
                slot_end = slot_start + service_duration
                
                # Check if slot conflicts with existing appointments
                conflict = db.query(Appointment).filter(
                    Appointment.stylist_id == stylist.id,
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                    or_(
                        and_(
                            Appointment.start_time <= slot_start,
                            Appointment.end_time > slot_start
                        ),
                        and_(
                            Appointment.start_time < slot_end,
                            Appointment.end_time >= slot_end
                        ),
                        and_(
                            Appointment.start_time >= slot_start,
                            Appointment.end_time <= slot_end
                        )
                    )
                ).first()
                
                if not conflict:
                    available_slots.append(
                        TimeSlot(
                            start_time=slot_start,
                            end_time=slot_end,
                            stylist_id=stylist.id,
                            stylist_name=stylist.full_name
                        )
                    )
                
                # Move to next slot (30 minutes later)
                slot_start += timedelta(minutes=30)
    
    return available_slots

@router.get("/{appointment_id}", response_model=AppointmentDetail)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_user)
):
    """
    Get appointment by ID
    
    Args:
        appointment_id: Appointment ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Appointment data
        
    Raises:
        HTTPException: If appointment not found or user not authorized
    """
    # Get the appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check authorization
    if current_user.role == UserRole.CLIENT and appointment.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this appointment"
        )
    
    if current_user.role == UserRole.STYLIST and appointment.stylist_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this appointment"
        )
    
    if current_user.role == UserRole.SALON_OWNER:
        # Check if appointment is for a stylist in one of their salons
        stylist = db.query(Stylist).filter(Stylist.id == appointment.stylist_id).first()
        salon = db.query(Salon).filter(Salon.id == stylist.salon_id).first()
        
        if salon.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this appointment"
            )
    
    return appointment

@router.put("/{appointment_id}/status", response_model=AppointmentDetail)
async def update_appointment_status(
    appointment_id: int,
    status_data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update appointment status
    
    Args:
        appointment_id: Appointment ID
        status_data: Status update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated appointment data
        
    Raises:
        HTTPException: If appointment not found or user not authorized
    """
    # Get the appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check authorization based on user role and requested status change
    if current_user.role == UserRole.CLIENT:
        # Clients can only cancel their own appointments
        if appointment.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
        
        # Clients can only cancel appointments
        if status_data.status != AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clients can only cancel appointments"
            )
    
    elif current_user.role == UserRole.STYLIST:
        # Stylists can only update their own appointments
        if appointment.stylist_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
        
        # Stylists can confirm, complete, or mark as no-show
        allowed_statuses = [AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW]
        if status_data.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Stylists can only confirm, complete, or mark appointments as no-show"
            )
    
    elif current_user.role == UserRole.SALON_OWNER:
        # Check if appointment is for a stylist in one of their salons
        stylist = db.query(Stylist).filter(Stylist.id == appointment.stylist_id).first()
        salon = db.query(Salon).filter(Salon.id == stylist.salon_id).first()
        
        if salon.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
    
    # Update appointment status
    appointment.status = status_data.status
    
    # Add cancellation reason if provided
    if status_data.status == AppointmentStatus.CANCELLED and status_data.cancellation_reason:
        appointment.cancellation_reason = status_data.cancellation_reason
    
    # Save changes
    db.commit()
    db.refresh(appointment)
    
    return appointment

@router.put("/{appointment_id}/payment", response_model=AppointmentDetail)
async def update_appointment_payment(
    appointment_id: int,
    payment_data: AppointmentPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_salon_staff)
):
    """
    Update appointment payment status (salon staff only)
    
    Args:
        appointment_id: Appointment ID
        payment_data: Payment update data
        db: Database session
        current_user: Current authenticated salon staff
        
    Returns:
        Updated appointment data
        
    Raises:
        HTTPException: If appointment not found or user not authorized
    """
    # Get the appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check authorization based on user role
    if current_user.role == UserRole.STYLIST:
        # Stylists can only update their own appointments
        if appointment.stylist_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
    
    elif current_user.role == UserRole.SALON_OWNER:
        # Check if appointment is for a stylist in one of their salons
        stylist = db.query(Stylist).filter(Stylist.id == appointment.stylist_id).first()
        salon = db.query(Salon).filter(Salon.id == stylist.salon_id).first()
        
        if salon.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
    
    # Update payment status
    appointment.is_paid = payment_data.is_paid
    
    # Save changes
    db.commit()
    db.refresh(appointment)
    
    return appointment