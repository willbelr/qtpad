#!/usr/bin/python3
import dbus
import sys

def main():
    try:
        # Verify if the bus already exist
        bus = dbus.SessionBus()
        session = bus.get_object("org.qtpad.session", "/org/qtpad/session")
        interface = dbus.Interface(session, "org.qtpad.session")

        # Handle command line input
        if len(sys.argv) > 2:
            interface.parse(sys.argv[1], sys.argv[2])
        sys.exit(0)

    except dbus.exceptions.DBusException:
        # Create a new instance
        import qtpad.application
        if len(sys.argv) > 2:
            qtpad.application.main(sys.argv[1], sys.argv[2])
        else:
            qtpad.application.main()

if __name__ == '__main__':
    main()
